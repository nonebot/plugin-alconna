from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.milky.utils import to_uri
from nonebot.adapters.milky.bot import Bot as MilkyBot
from nonebot.adapters.milky.event import Event as MilkyEvent
from nonebot.adapters.milky.model.api import MessageResponse
from nonebot.adapters.milky.message import Message, MessageSegment
from nonebot.adapters.milky.event import MessageEvent, MessageRecallEvent

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export
from nonebot_plugin_alconna.uniseg.segment import (
    At,
    File,
    Text,
    AtAll,
    Audio,
    Emoji,
    Image,
    Reply,
    Video,
    Voice,
    RefNode,
    Reference,
)


class MilkyMessageExporter(MessageExporter["Message"]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.milky

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        assert isinstance(event, MilkyEvent)
        if isinstance(event, (MessageEvent, MessageRecallEvent)):
            return Target(
                str(event.data.peer_id),
                private=event.is_private,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        if event.is_private:
            return Target(
                event.get_user_id(),
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        if group_id := getattr(event.data, "group_id", None):
            return Target(
                str(group_id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MilkyEvent)
        if (message_seq := getattr(event.data, "message_seq", None)) is not None:
            if isinstance(event, MessageEvent):
                return f"{message_seq}@{event.data.message_scene}:{event.data.peer_id}"
            return str(message_seq)
        raise NotImplementedError

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag != "user":
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="at", seg=seg))
        return MessageSegment.mention(int(seg.target))

    @export
    async def at_all(self, seg: AtAll, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.mention_all()

    @export
    async def emoji(self, seg: Emoji, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.face(seg.id)

    @export
    async def media(self, seg: Union[Image, Voice, Audio], bot: Union[Bot, None]) -> "MessageSegment":
        assert isinstance(bot, MilkyBot)
        name = seg.__class__.__name__.lower()
        method = {
            "image": MessageSegment.image,
            "voice": MessageSegment.record,
            "audio": MessageSegment.record,
        }[name]
        if seg.raw:
            return method(raw=seg.raw)
        if seg.path:
            return method(path=Path(seg.path))
        if seg.url:
            return method(seg.url)
        if seg.id:
            url = await bot.get_resource_temp_url(seg.id)
            return method(url)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def video(self, seg: Video, bot: Union[Bot, None]) -> "MessageSegment":
        assert isinstance(bot, MilkyBot)
        thumb_url = None
        if seg.thumbnail:
            if seg.thumbnail.url:
                thumb_url = seg.thumbnail.url
            elif seg.thumbnail.id:
                thumb_url = await bot.get_resource_temp_url(seg.thumbnail.id)
            elif seg.__class__.to_url and seg.thumbnail.raw:
                thumb_url = await seg.__class__.to_url(
                    seg.thumbnail.raw,
                    bot,
                    None if seg.thumbnail.name == seg.thumbnail.__default_name__ else seg.thumbnail.name,
                )
            elif seg.__class__.to_url and seg.thumbnail.path:
                thumb_url = await seg.__class__.to_url(
                    seg.thumbnail.path,
                    bot,
                    None if seg.thumbnail.name == seg.thumbnail.__default_name__ else seg.thumbnail.name,
                )
        if seg.raw:
            return MessageSegment.video(raw=seg.raw, thumb_url=thumb_url)
        if seg.path:
            return MessageSegment.video(path=Path(seg.path), thumb_url=thumb_url)
        if seg.url:
            return MessageSegment.video(seg.url, thumb_url=thumb_url)
        if seg.id:
            url = await bot.get_resource_temp_url(seg.id)
            return MessageSegment.video(url, thumb_url=thumb_url)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="video", seg=seg))

    @export
    async def file(self, seg: File, bot: Union[Bot, None]) -> "MessageSegment":
        filename = seg.name if seg.name != seg.__default_name__ else None
        if seg.path:
            return MessageSegment(
                "$milky:file", {"uri": Path(seg.path).resolve().as_uri(), "name": filename or Path(seg.path).name}
            )
        if filename is None:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="file", seg=seg))
        if seg.url:
            return MessageSegment("$milky:file", {"uri": seg.url, "name": filename})
        if seg.raw:
            if seg.__class__.to_url:
                return MessageSegment(
                    "$milky:file",
                    {
                        "uri": await seg.__class__.to_url(
                            seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name
                        ),
                        "name": filename,
                    },
                )
            return MessageSegment("$milky:file", {"uri": to_uri(raw=seg.raw_bytes), "name": filename})
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="file", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        message_seq, *_ = seg.id.split("@")
        return MessageSegment.reply(int(message_seq))

    @export
    async def reference(self, seg: Reference, bot: Union[Bot, None]) -> "MessageSegment":
        assert isinstance(bot, MilkyBot)
        if seg.id:
            messages = await bot.get_forwarded_messages(forward_id=seg.id)
            return MessageSegment.forward(
                [MessageSegment.node(int(bot.self_id) if bot else 10001, msg.name, msg.message) for msg in messages]
            )
        if not seg.children:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="forward", seg=seg))
        messages = []
        for node in seg.children:
            if isinstance(node, RefNode):
                if not node.context:
                    continue
                source = await bot.get_message(
                    message_scene="group", peer_id=int(node.context), message_seq=int(node.id)
                )
                messages.append(MessageSegment.node(source.sender_id, source.sender.nickname, source.message))
            else:
                content = self.get_message_type()()
                if isinstance(node.content, str):
                    content.extend(self.get_message_type()(node.content))
                else:
                    content.extend(await self.export(node.content, bot, True))
                messages.append(MessageSegment.node(user_id=int(node.uid), name=node.name, segments=content))
        if not messages:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="forward", seg=seg))
        return MessageSegment.forward(messages)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, MilkyBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, Event):
            _target = self.get_target(target, bot)
        else:
            _target = target

        if msg := message.include("milky:file"):
            if _target.private:
                file_id = await bot.upload_private_file(
                    user_id=int(_target.id),
                    url=msg[0].data["uri"],
                    file_name=msg[0].data["name"],
                    **kwargs,
                )
            else:
                file_id = await bot.upload_group_file(
                    group_id=int(_target.id),
                    url=msg[0].data["uri"],
                    file_name=msg[0].data["name"],
                    **kwargs,
                )
            return File(file_id)
        if isinstance(target, Event):
            return await bot.send(target, message, **kwargs)  # type: ignore
        if _target.private:
            return await bot.send_private_message(user_id=int(_target.id), message=message, **kwargs)
        return await bot.send_group_message(group_id=int(_target.id), message=message, **kwargs)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, MilkyBot)
        if isinstance(mid, File) and mid.id:
            if isinstance(context, Target):
                if not context.private:
                    group_id = int(context.id)
                    await bot.delete_group_file(group_id=group_id, file_id=mid.id)
            elif not context.is_private:  # type: ignore
                group_id = int(getattr(context.data, "group_id", -1))  # type: ignore
                await bot.delete_group_file(group_id=group_id, file_id=mid.id)
            return
        if isinstance(mid, MessageResponse):
            message_seq = mid.message_seq
        elif isinstance(mid, int):
            message_seq = mid
        elif isinstance(mid, str):
            message_seq, _, target = mid.partition("@")
            message_seq = int(message_seq)
            if target:
                scene, _, peer_id = target.partition(":")
                if scene == "group":
                    await bot.recall_group_message(group_id=int(peer_id), message_seq=message_seq)
                else:
                    await bot.recall_private_message(user_id=int(peer_id), message_seq=message_seq)
                return
        else:
            return
        if isinstance(context, Target):
            if context.private:
                user_id = int(context.id)
                await bot.recall_private_message(user_id=user_id, message_seq=message_seq)
            else:
                group_id = int(context.id)
                await bot.recall_group_message(group_id=group_id, message_seq=message_seq)
        elif isinstance(context, MilkyEvent):
            if context.is_private:
                user_id = int(context.get_user_id())
                await bot.recall_private_message(user_id=user_id, message_seq=message_seq)
            else:
                group_id = int(getattr(context.data, "group_id", -1))
                await bot.recall_group_message(group_id=group_id, message_seq=message_seq)

    async def reaction(self, emoji: Emoji, mid: Any, bot: Bot, context: Union[Target, Event], delete: bool = False):
        assert isinstance(bot, MilkyBot)

        if isinstance(context, Target):
            if context.private:
                return
            group_id = int(context.id)
        elif isinstance(context, MilkyEvent):
            if context.is_private:
                return
            group_id = int(getattr(context.data, "group_id", -1))  # type: ignore
        else:
            return
        if isinstance(mid, MessageResponse):
            message_seq = mid.message_seq
        elif isinstance(mid, int):
            message_seq = mid
        elif isinstance(mid, str):
            message_seq, _, target = mid.partition("@")
            message_seq = int(message_seq)
            if target:
                scene, _, peer_id = target.partition(":")
                if scene == "group":
                    group_id = int(peer_id)
                else:
                    return
        else:
            return
        await bot.send_group_message_reaction(
            group_id=group_id, message_seq=message_seq, reaction=emoji.id, is_add=not delete
        )

    def get_reply(self, mid: Any):
        if isinstance(mid, MessageResponse):
            return Reply(str(mid.message_seq), origin=mid)
        if isinstance(mid, int):
            return Reply(str(mid))
        if isinstance(mid, str):
            return Reply(mid)
        raise ValueError(f"Invalid message id: {mid}")
