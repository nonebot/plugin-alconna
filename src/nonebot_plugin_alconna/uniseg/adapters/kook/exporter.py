from typing import TYPE_CHECKING, Any, Union, cast

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.kaiheila.bot import Bot as KBot
from nonebot.adapters.kaiheila.api.model import MessageCreateReturn
from nonebot.adapters.kaiheila.event import MessageEvent, PrivateMessageEvent
from nonebot.adapters.kaiheila.message import Message, MessageSegment, MessageSerializer

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export
from nonebot_plugin_alconna.uniseg.segment import At, File, Text, AtAll, Audio, Emoji, Hyper, Image, Reply, Video, Voice


class KookMessageExporter(MessageExporter["Message"]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.kook

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.msg_id)

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if group_id := getattr(event, "group_id", None):
            return Target(
                str(group_id), adapter=self.get_adapter(), self_id=bot.self_id if bot else None, scope=SupportScope.kook
            )
        if user_id := getattr(event, "user_id", None):
            return Target(
                str(user_id),
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.kook,
            )
        raise NotImplementedError

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        if seg.extract_most_style() == "markdown":
            return MessageSegment.KMarkdown(seg.text)
        elif seg.styles:
            return MessageSegment.KMarkdown(str(seg))
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        if seg.flag == "role":
            return MessageSegment.mention_role(seg.target)
        elif seg.flag == "channel":
            return MessageSegment.KMarkdown(f"(chn){seg.target}(chn)")
        else:
            return MessageSegment.mention(seg.target)

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        return MessageSegment.mention_here() if seg.here else MessageSegment.mention_all()

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        if seg.name:
            return MessageSegment.KMarkdown(f"(emj){seg.name}(emj)[{seg.id}]")
        else:
            return MessageSegment.KMarkdown(f":{seg.id}:")

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Bot) -> "MessageSegment":
        if TYPE_CHECKING:
            assert isinstance(bot, KBot)
        name = seg.__class__.__name__.lower()
        method = {
            "image": MessageSegment.image,
            "voice": MessageSegment.audio,
            "audio": MessageSegment.audio,
            "video": MessageSegment.video,
            "file": MessageSegment.file,
        }[name]
        if seg.id or seg.url:
            return method(seg.id or seg.url)
        if seg.__class__.to_url and seg.raw:
            return method(
                await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name)
            )
        if seg.__class__.to_url and seg.path:
            return method(
                await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name)
            )
        local_method = {
            "image": MessageSegment.local_image,
            "voice": MessageSegment.local_audio,
            "audio": MessageSegment.local_audio,
            "video": MessageSegment.local_video,
            "file": MessageSegment.local_file,
        }[name]
        if seg.raw:
            return local_method(seg.raw_bytes)
        elif seg.path:
            return local_method(seg.path)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def hyper(self, seg: Hyper, bot: Bot) -> "MessageSegment":
        if seg.format == "xml":
            raise SerializeFailed(
                lang.require("nbp-uniseg", "failed_segment").format(adapter="kook", seg=seg, target="Card")
            )
        return MessageSegment.Card(seg.content or seg.raw)

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        return MessageSegment.quote(seg.id)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        assert isinstance(bot, KBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, Event):
            target = self.get_target(target, bot)

        if target.private:
            return await bot.send_msg(message_type="private", user_id=target.id, message=message)
        else:
            return await bot.send_msg(message_type="channel", channel_id=target.id, message=message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        _mid: MessageCreateReturn = cast(MessageCreateReturn, mid)

        assert _mid.msg_id

        assert isinstance(bot, KBot)
        if isinstance(context, Target):
            if context.private:
                await bot.directMessage_delete(msg_id=_mid.msg_id)
            else:
                await bot.message_delete(msg_id=_mid.msg_id)
        elif isinstance(context, PrivateMessageEvent):
            await bot.directMessage_delete(msg_id=_mid.msg_id)
        else:
            await bot.message_delete(msg_id=_mid.msg_id)
        return

    async def edit(self, new: Message, mid: Any, bot: Bot, context: Union[Target, Event]):
        if TYPE_CHECKING:
            assert isinstance(new, self.get_message_type())
            assert isinstance(bot, KBot)

        _mid: MessageCreateReturn = cast(MessageCreateReturn, mid)
        if not _mid.msg_id:
            return
        data = await MessageSerializer(new).serialize(bot=bot)
        data.pop("type", None)
        data["msg_id"] = _mid.msg_id
        if isinstance(context, Target):
            if context.private:
                data.pop("quote", None)
                await bot.directMessage_update(**data)
            else:
                await bot.message_update(**data)
        elif isinstance(context, PrivateMessageEvent):
            data.pop("quote", None)
            await bot.directMessage_update(**data)
        else:
            await bot.message_update(**data)
        return

    def get_reply(self, mid: Any):
        _mid: MessageCreateReturn = cast(MessageCreateReturn, mid)
        if not _mid.msg_id:
            raise NotImplementedError
        return Reply(_mid.msg_id)
