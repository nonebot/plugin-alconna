from typing import TYPE_CHECKING, Any, Union, cast

from tarina import lang
from nonebot.adapters import Bot, Event, Message

from ..export import Target, MessageExporter, SerializeFailed, export
from ..segment import At, Card, File, Text, AtAll, Audio, Emoji, Image, Reply, Video, Voice

if TYPE_CHECKING:
    from nonebot.adapters.kaiheila.message import MessageSegment


class KookMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.kaiheila.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "Kaiheila"

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.kaiheila.event import MessageEvent

        assert isinstance(event, MessageEvent)
        return str(event.msg_id)

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if group_id := getattr(event, "group_id", None):
            return Target(str(group_id), platform=self.get_adapter(), self_id=bot.self_id if bot else None)
        if user_id := getattr(event, "user_id", None):
            return Target(
                str(user_id), private=True, platform=self.get_adapter(), self_id=bot.self_id if bot else None
            )
        raise NotImplementedError

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if seg.style and "markdown" in seg.style:
            return ms.KMarkdown(seg.text)
        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if seg.flag == "role":
            return ms.mention_role(seg.target)
        elif seg.flag == "channel":
            return ms.KMarkdown(f"(chn){seg.target}(chn)")
        else:
            return ms.mention(seg.target)

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.mention_here() if seg.here else ms.mention_all()

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.name:
            return ms.KMarkdown(f"(emj){seg.name}(emj)[{seg.id}]")
        else:
            return ms.KMarkdown(f":{seg.id}:")

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if TYPE_CHECKING:
            from nonebot.adapters.kaiheila.bot import Bot as KBot

            assert isinstance(bot, KBot)
        name = seg.__class__.__name__.lower()

        if seg.id or seg.url:
            method = {
                "image": ms.image,
                "voice": ms.audio,
                "audio": ms.audio,
                "video": ms.video,
                "file": ms.file,
            }[name]
            return method(seg.id or seg.url)
        method = {
            "image": ms.local_image,
            "voice": ms.local_audio,
            "audio": ms.local_audio,
            "video": ms.local_video,
            "file": ms.local_file,
        }[name]
        if seg.raw:
            return method(seg.raw_bytes)
        elif seg.path:
            return method(seg.path)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def card(self, seg: Card, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.flag == "xml":
            raise SerializeFailed(
                lang.require("nbp-uniseg", "failed_segment").format(adapter="kook", seg=seg, target="Card")
            )
        return ms.Card(seg.raw)

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.quote(seg.id)

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.kaiheila.bot import Bot as KBot

        assert isinstance(bot, KBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())
        if target.private:
            return await bot.send_msg(message_type="private", user_id=target.id, message=message)
        else:
            return await bot.send_msg(message_type="channel", channel_id=target.id, message=message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        from nonebot.adapters.kaiheila.bot import Bot as KBot
        from nonebot.adapters.kaiheila.event import PrivateMessageEvent
        from nonebot.adapters.kaiheila.api.model import MessageCreateReturn

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
        from nonebot.adapters.kaiheila.bot import Bot as KBot
        from nonebot.adapters.kaiheila.event import PrivateMessageEvent
        from nonebot.adapters.kaiheila.message import MessageSerializer
        from nonebot.adapters.kaiheila.api.model import MessageCreateReturn

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
        from nonebot.adapters.kaiheila.api.model import MessageCreateReturn

        _mid: MessageCreateReturn = cast(MessageCreateReturn, mid)
        if not _mid.msg_id:
            raise NotImplementedError
        return Reply(_mid.msg_id)
