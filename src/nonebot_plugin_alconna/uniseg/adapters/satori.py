from typing import TYPE_CHECKING, Any, Union, cast

from tarina import lang
from nonebot.adapters import Bot, Event, Message

from ..export import Target, MessageExporter, SerializeFailed, export
from ..segment import At, File, Text, AtAll, Audio, Image, Reply, Video, Voice, RefNode, Reference

if TYPE_CHECKING:
    from nonebot.adapters.satori.message import MessageSegment


class SatoriMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.satori.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "Satori"

    def get_target(self, event: Event) -> Target:
        from nonebot.adapters.satori.event import NoticeEvent, MessageEvent

        if isinstance(event, (MessageEvent, NoticeEvent)):
            if event.channel:
                return Target(
                    event.channel.id, event.guild.id if event.guild else event.channel.parent_id or ""
                )
            elif event.user:
                return Target(event.user.id, private=True)
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.satori.event import MessageEvent

        assert isinstance(event, MessageEvent)
        return str(event.message.id)

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        from nonebot.adapters.satori.message import STYLE_TYPE_MAP

        ms = self.segment_class

        if not seg.style:
            return ms.text(seg.text)
        if seg.style == "br" or seg.text == "\n":
            return ms.br()
        if seg.style in STYLE_TYPE_MAP:
            seg_cls, seg_type = STYLE_TYPE_MAP[seg.style]
            return seg_cls(seg_type, {"text": seg.text})
        if hasattr(ms, seg.style):
            return getattr(ms, seg.style)(seg.text)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=seg.style, seg=seg))

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if seg.flag == "role":
            return ms.at_role(seg.target, seg.display)
        if seg.flag == "channel":
            return ms.sharp(seg.target, seg.display)
        return ms.at(seg.target, seg.display)

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.at_all(seg.here)

    @export
    async def res(self, seg: Union[Image, Voice, Video, Audio, File], bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        name = seg.__class__.__name__.lower()
        method = {
            "image": ms.image,
            "voice": ms.audio,
            "video": ms.video,
            "audio": ms.audio,
            "file": ms.file,
        }[name]
        if seg.id or seg.url:
            return method(url=seg.id or seg.url)
        if seg.path:
            return method(path=seg.path)
        if seg.raw:
            data = seg.raw_bytes
            if seg.mimetype:
                return method(raw={"data": data, "mime": seg.mimetype})
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.quote(seg.id, content=seg.msg)  # type: ignore

    @export
    async def reference(self, seg: Reference, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if isinstance(seg.content, str):
            content = self.get_message_type()(seg.content)
        elif isinstance(seg.content, list):
            content = self.get_message_type()()
            for node in seg.content:
                if isinstance(node, RefNode):
                    content.append(ms.message(node.id))
                else:
                    _content = self.get_message_type()()
                    _content.append(ms.author(node.uid, node.name))
                    if isinstance(node.content, str):
                        _content.extend(self.get_message_type()(node.content))
                    elif isinstance(node.content, list):
                        _content.extend(await self.export(node.content, bot, True))  # type: ignore
                    else:
                        _content.extend(node.content)
                    content.append(ms.message(content=_content))
        else:
            content = seg.content
        return ms.message(seg.id, bool(seg.content), content)

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.satori.bot import Bot as SatoriBot

        assert isinstance(bot, SatoriBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if target.private:
            return await bot.send_private_message(target.id, message)
        else:
            return await bot.send_message(target.id, message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        from nonebot.adapters.satori.models import InnerMessage
        from nonebot.adapters.satori.bot import Bot as SatoriBot

        assert isinstance(bot, SatoriBot)
        _mid: InnerMessage = cast(InnerMessage, mid)
        if isinstance(context, Target):
            if context.private:
                channel = await bot.user_channel_create(user_id=context.id)
                await bot.message_delete(channel_id=channel.id, message_id=_mid.id)
            else:
                await bot.message_delete(channel_id=context.id, message_id=_mid.id)
        else:
            channel = _mid.channel or context.channel  # type: ignore
            await bot.message_delete(channel_id=channel.id, message_id=_mid.id)
        return

    async def edit(self, new: Message, mid: Any, bot: Bot, context: Union[Target, Event]):
        from nonebot.adapters.satori.models import InnerMessage
        from nonebot.adapters.satori.bot import Bot as SatoriBot

        assert isinstance(bot, SatoriBot)
        if TYPE_CHECKING:
            assert isinstance(new, self.get_message_type())

        _mid: InnerMessage = cast(InnerMessage, mid)
        if isinstance(context, Target):
            if context.private:
                channel = await bot.user_channel_create(user_id=context.id)
                return await bot.update_message(channel.id, _mid.id, new)
            return await bot.update_message(context.id, _mid.id, new)
        channel = mid.channel or context.channel  # type: ignore
        return await bot.update_message(channel.id, _mid.id, new)
