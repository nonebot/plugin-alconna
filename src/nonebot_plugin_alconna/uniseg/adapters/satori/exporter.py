from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence, Union, cast

from nonebot.adapters import Bot, Event
from nonebot.adapters.satori.bot import Bot as SatoriBot
from nonebot.adapters.satori.event import InteractionCommandMessageEvent, MessageEvent, NoticeEvent, ReactionEvent
from nonebot.adapters.satori.message import STYLE_TYPE_MAP, Message, MessageSegment
from nonebot.adapters.satori.message import Text as _Text
from nonebot.adapters.satori.models import ChannelType, MessageObject
from tarina import lang

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter, SerializeFailed, SupportAdapter, export
from nonebot_plugin_alconna.uniseg.segment import (
    At,
    AtAll,
    Audio,
    Button,
    Emoji,
    File,
    Image,
    Keyboard,
    Reference,
    RefNode,
    Reply,
    Segment,
    Text,
    Video,
    Voice,
)
from nonebot_plugin_alconna.uniseg.target import Target


class SatoriMessageExporter(MessageExporter[Message]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.satori

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if TYPE_CHECKING:
            assert isinstance(bot, SatoriBot)
        if isinstance(event, (MessageEvent, NoticeEvent)):
            if event.channel:
                if event.channel.type == ChannelType.DIRECT:
                    return Target(
                        event.user.id,  # type: ignore
                        parent_id=event.channel.id,
                        private=True,
                        adapter=self.get_adapter(),
                        self_id=bot.self_id if bot else None,
                        platform=bot.platform if bot else None,
                        scope=SupportScope.ensure_satori(bot.platform) if bot else SupportScope.satori_other,
                    )
                return Target(
                    event.channel.id,
                    (event.guild.id if event.guild else event.channel.parent_id) or "",
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    platform=bot.platform if bot else None,
                    scope=SupportScope.ensure_satori(bot.platform) if bot else SupportScope.satori_other,
                )
            if event.user:
                return Target(
                    event.user.id,
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    platform=bot.platform if bot else None,
                    scope=SupportScope.ensure_satori(bot.platform) if bot else SupportScope.satori_other,
                )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, (MessageEvent, ReactionEvent, InteractionCommandMessageEvent))
        return str(event.message.id)

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]):
        if not seg.styles:
            return MessageSegment.text(seg.text)
        if seg.extract_most_style() == "markdown":
            return _Text("text", {"text": seg.text, "styles": {(0, len(seg.text)): ["chronocat:markdown"]}})
        res = Message()
        for part in seg.style_split():
            if part.extract_most_style() == "br":
                res.append(MessageSegment.br())
            elif part.extract_most_style() == "link":
                if not getattr(part, "_children", []):
                    res.append(MessageSegment.link(part.text))
                else:
                    res.append(MessageSegment.link(part.text, part._children[0].text))  # type: ignore
            else:
                styles = part.styles.copy()
                for scale, style in part.styles.items():
                    styles[scale] = [STYLE_TYPE_MAP.get(s, s) for s in style]
                res.append(_Text("text", {"text": part.text, "styles": styles}))
        res.__merge_text__()
        return res

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag == "role":
            return MessageSegment.at_role(seg.target, seg.display)
        if seg.flag == "channel":
            return MessageSegment.sharp(seg.target, seg.display)
        return MessageSegment.at(seg.target, seg.display)

    @export
    async def at_all(self, seg: AtAll, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.at_all(seg.here)

    @export
    async def button(self, seg: Button, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag == "action" and seg.id:
            return MessageSegment.action_button(seg.id, seg.style)(await self.export(seg.children, bot, True))  # type: ignore
        if seg.flag == "link" and seg.url:
            return MessageSegment.link_button(seg.url, seg.style)(await self.export(seg.children, bot, True))  # type: ignore
        if seg.text:
            return MessageSegment.input_button(seg.text, seg.style)(await self.export(seg.children, bot, True))  # type: ignore
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="button", seg=seg))

    @export
    async def keyboard(self, seg: Keyboard, bot: Union[Bot, None]):
        if seg.children:
            return [await self.button(child, bot) for child in seg.children]
        return MessageSegment.text("")

    @export
    async def res(self, seg: Union[Image, Voice, Video, Audio, File], bot: Union[Bot, None]) -> "MessageSegment":
        name = seg.__class__.__name__.lower()
        method = {
            "image": MessageSegment.image,
            "voice": MessageSegment.audio,
            "video": MessageSegment.video,
            "audio": MessageSegment.audio,
            "file": MessageSegment.file,
        }[name]
        filename = None if seg.name == seg.__default_name__ else seg.name
        if seg.id or seg.url:
            ans = method(url=seg.id or seg.url, name=filename)(await self.export(seg.children, bot, True))  # type: ignore
        elif seg.__class__.to_url and seg.path:
            filename = filename or Path(seg.path).name
            ans = method(
                await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name),
                name=filename,
            )(
                await self.export(seg.children, bot, True)  # type: ignore
            )  # type: ignore
        elif seg.__class__.to_url and seg.raw:
            ans = method(
                await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name),
                name=filename,
            )(
                await self.export(seg.children, bot, True)  # type: ignore
            )  # type: ignore
        elif seg.path:
            filename = filename or Path(seg.path).name
            ans = method(path=seg.path, name=filename)(await self.export(seg.children, bot, True))  # type: ignore
        elif seg.raw and seg.mimetype:
            data = seg.raw_bytes
            ans = method(raw=data, mime=seg.mimetype, name=filename)(await self.export(seg.children, bot, True))  # type: ignore
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))
        # if isinstance(seg, Image) and seg.sticker:
        #     ans.data["subType"] = 1
        return ans

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.quote(seg.id, content=seg.msg)  # type: ignore

    @export
    async def reference(self, seg: Reference, bot: Union[Bot, None]) -> "MessageSegment":
        content = self.get_message_type()()
        for node in seg.children:
            if isinstance(node, RefNode):
                content.append(MessageSegment.message(node.id))
            else:
                _content = self.get_message_type()()
                _content.append(MessageSegment.author(node.uid, node.name))
                if isinstance(node.content, str):
                    _content.extend(self.get_message_type()(node.content))
                else:
                    _content.extend(await self.export(node.content, bot, True))
                content.append(MessageSegment.message(content=_content))

        return MessageSegment.message(seg.id, bool(seg.children), content)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, SatoriBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, Event):
            return await bot.send(target, message, **kwargs)  # type: ignore

        if target.private:
            return await bot.send_private_message(target.id, message)
        return await bot.send_message(target.id, message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, SatoriBot)
        if isinstance(context, (MessageEvent, NoticeEvent)) and context.channel and isinstance(mid, str):
            await bot.message_delete(channel_id=context.channel.id, message_id=mid)
            return
        _mid: MessageObject = cast(MessageObject, mid)
        if isinstance(context, Target):
            if context.private:
                channel = await bot.user_channel_create(user_id=context.id)
                await bot.message_delete(channel_id=channel.id, message_id=_mid.id)
            else:
                await bot.message_delete(channel_id=context.id, message_id=_mid.id)
        elif isinstance(context, (MessageEvent, NoticeEvent)) and context.channel:
            channel = _mid.channel or context.channel
            await bot.message_delete(channel_id=channel.id, message_id=_mid.id)

    async def edit(self, new: Sequence[Segment], mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, SatoriBot)
        new_msg = await self.export(new, bot, True)
        if isinstance(context, (MessageEvent, NoticeEvent)) and context.channel and isinstance(mid, str):
            return await bot.update_message(context.channel.id, mid, new_msg)
        _mid: MessageObject = cast(MessageObject, mid)
        if isinstance(context, Target):
            channel_id = mid.channel.id if mid.channel else context.id
            if context.private:
                channel_id = (await bot.user_channel_create(user_id=context.id)).id
            return await bot.update_message(channel_id, _mid.id, new_msg)
        if isinstance(context, (MessageEvent, NoticeEvent)) and context.channel:
            channel = mid.channel or context.channel
            return await bot.update_message(channel.id, _mid.id, new_msg)

    async def reaction(self, emoji: Emoji, mid: Any, bot: Bot, context: Union[Target, Event], delete: bool = False):
        assert isinstance(bot, SatoriBot)
        if isinstance(context, (MessageEvent, NoticeEvent)) and context.channel and isinstance(mid, str):
            if delete:
                return await bot.reaction_delete(
                    channel_id=context.channel.id, message_id=mid, emoji=emoji.name or emoji.id
                )
            return await bot.reaction_create(
                channel_id=context.channel.id, message_id=mid, emoji=emoji.name or emoji.id
            )
        _mid: MessageObject = cast(MessageObject, mid)
        if isinstance(context, Target):
            channel_id = mid.channel.id if mid.channel else context.id
            if context.private:
                channel_id = (await bot.user_channel_create(user_id=context.id)).id
            if delete:
                return await bot.reaction_delete(
                    channel_id=channel_id, message_id=_mid.id, emoji=emoji.name or emoji.id
                )
            return await bot.reaction_create(channel_id=channel_id, message_id=_mid.id, emoji=emoji.name or emoji.id)
        if isinstance(context, (MessageEvent, NoticeEvent)) and context.channel:
            channel = mid.channel or context.channel
            if delete:
                return await bot.reaction_delete(
                    channel_id=channel.id, message_id=_mid.id, emoji=emoji.name or emoji.id
                )
            return await bot.reaction_create(channel_id=channel.id, message_id=_mid.id, emoji=emoji.name or emoji.id)

    def get_reply(self, mid: Any):
        _mid: MessageObject = cast(MessageObject, mid)
        return Reply(_mid.id)
