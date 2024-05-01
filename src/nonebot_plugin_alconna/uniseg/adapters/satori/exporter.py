from typing import TYPE_CHECKING, Any, Union, cast

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.satori.bot import Bot as SatoriBot
from nonebot.adapters.satori.message import Text as _Text
from nonebot.adapters.satori.message import STYLE_TYPE_MAP
from nonebot.adapters.satori.event import NoticeEvent, MessageEvent
from nonebot.adapters.satori.message import Message, MessageSegment
from nonebot.adapters.satori.models import ChannelType, InnerMessage

from nonebot_plugin_alconna.uniseg.target import Target
from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import SupportAdapter, MessageExporter, SerializeFailed, export
from nonebot_plugin_alconna.uniseg.segment import (
    At,
    File,
    Text,
    AtAll,
    Audio,
    Image,
    Reply,
    Video,
    Voice,
    RefNode,
    Reference,
)


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
            elif event.user:
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
        assert isinstance(event, MessageEvent)
        return str(event.message.id)

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        if not seg.styles:
            return MessageSegment.text(seg.text)
        if seg.extract_most_style() == "link":
            if not getattr(seg, "_children", []):
                return MessageSegment.link(seg.text)
            else:
                return MessageSegment.link(seg.text, seg._children[0].text)  # type: ignore
        if seg.extract_most_style() == "markdown":
            return _Text("text", {"text": seg.text, "styles": {(0, len(seg.text)): ["chronocat:markdown"]}})
        styles = seg.styles.copy()
        for scale, style in seg.styles.items():
            styles[scale] = [STYLE_TYPE_MAP.get(s, s) for s in style]
        return _Text("text", {"text": seg.text, "styles": styles})

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        if seg.flag == "role":
            return MessageSegment.at_role(seg.target, seg.display)
        if seg.flag == "channel":
            return MessageSegment.sharp(seg.target, seg.display)
        return MessageSegment.at(seg.target, seg.display)

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        return MessageSegment.at_all(seg.here)

    @export
    async def res(self, seg: Union[Image, Voice, Video, Audio, File], bot: Bot) -> "MessageSegment":
        name = seg.__class__.__name__.lower()
        method = {
            "image": MessageSegment.image,
            "voice": MessageSegment.audio,
            "video": MessageSegment.video,
            "audio": MessageSegment.audio,
            "file": MessageSegment.file,
        }[name]
        if seg.id or seg.url:
            return method(url=seg.id or seg.url)(await self.export(seg.children, bot, True))  # type: ignore
        if seg.__class__.to_url and seg.path:
            return method(
                await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name)
            )(
                await self.export(seg.children, bot, True)  # type: ignore
            )  # type: ignore
        if seg.__class__.to_url and seg.raw:
            return method(
                await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name)
            )(
                await self.export(seg.children, bot, True)  # type: ignore
            )  # type: ignore
        if seg.path:
            return method(path=seg.path)(await self.export(seg.children, bot, True))  # type: ignore
        if seg.raw:
            data = seg.raw_bytes
            if seg.mimetype:
                return method(raw=data, mime=seg.mimetype)(await self.export(seg.children, bot, True))  # type: ignore
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        return MessageSegment.quote(seg.id, content=seg.msg)  # type: ignore

    @export
    async def reference(self, seg: Reference, bot: Bot) -> "MessageSegment":
        content = self.get_message_type()()
        for node in seg.children:
            if isinstance(node, RefNode):
                content.append(MessageSegment.message(node.id))
            else:
                _content = self.get_message_type()()
                _content.append(MessageSegment.author(node.uid, node.name))
                if isinstance(node.content, str):
                    _content.extend(self.get_message_type()(node.content))
                elif isinstance(node.content, list):
                    _content.extend(await self.export(node.content, bot, True))  # type: ignore
                else:
                    _content.extend(node.content)
                content.append(MessageSegment.message(content=_content))

        return MessageSegment.message(seg.id, bool(seg.children), content)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        assert isinstance(bot, SatoriBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, Event):
            target = self.get_target(target, bot)

        if target.private:
            return await bot.send_private_message(target.id, message)
        else:
            return await bot.send_message(target.id, message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, SatoriBot)
        _mid: InnerMessage = cast(InnerMessage, mid)
        if isinstance(context, Target):
            if context.private:
                channel = await bot.user_channel_create(user_id=context.id)
                await bot.message_delete(channel_id=channel.id, message_id=_mid.id)
            else:
                await bot.message_delete(channel_id=context.id, message_id=_mid.id)
        else:
            if TYPE_CHECKING:
                assert isinstance(context, MessageEvent)
            channel = _mid.channel or context.channel
            await bot.message_delete(channel_id=channel.id, message_id=_mid.id)
        return

    async def edit(self, new: Message, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, SatoriBot)
        if TYPE_CHECKING:
            assert isinstance(new, self.get_message_type())

        _mid: InnerMessage = cast(InnerMessage, mid)
        if isinstance(context, Target):
            if context.private:
                channel = await bot.user_channel_create(user_id=context.id)
                return await bot.update_message(channel.id, _mid.id, new)
            return await bot.update_message(context.id, _mid.id, new)
        if TYPE_CHECKING:
            assert isinstance(context, MessageEvent)
        channel = mid.channel or context.channel
        return await bot.update_message(channel.id, _mid.id, new)

    def get_reply(self, mid: Any):
        _mid: InnerMessage = cast(InnerMessage, mid)
        return Reply(_mid.id)
