from pathlib import Path
from typing import TYPE_CHECKING, Any, Union, cast

from tarina import lang
from nonebot.internal.driver import Request
from nonebot.adapters import Bot, Event, Message

from ..export import Target, MessageExporter, SerializeFailed, export
from ..segment import At, File, Text, AtAll, Audio, Emoji, Image, Reply, Video, Voice

if TYPE_CHECKING:
    from nonebot.adapters.discord.message import MessageSegment


class DiscordMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.discord.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "Discord"

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.discord.event import MessageEvent

        assert isinstance(event, MessageEvent)
        return str(event.message_id)

    def get_target(self, event: Event) -> Target:
        from nonebot.adapters.discord.api.model import Channel
        from nonebot.adapters.discord.event import MessageEvent, GuildMessageCreateEvent

        if isinstance(event, MessageEvent):
            if isinstance(event, GuildMessageCreateEvent):
                return Target(str(event.channel_id), str(event.guild_id), channel=True)
            return Target(str(event.channel_id), channel=True)
        elif isinstance(event, Channel):
            return Target(str(event.id), channel=True)
        raise NotImplementedError

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.flag == "role":
            return ms.mention_role(int(seg.target))
        elif seg.flag == "channel":
            return ms.mention_channel(int(seg.target))
        else:
            return ms.mention_user(int(seg.target))

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.mention_everyone()

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.custom_emoji(seg.name or "", seg.id)

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        name = seg.__class__.__name__.lower()

        if seg.raw and (seg.id or seg.name):
            content = seg.raw_bytes
            return ms.attachment(seg.id or seg.name, content=content)
        elif seg.path:
            path = Path(seg.path)
            return ms.attachment(path.name, content=path.read_bytes())
        elif seg.url and (seg.id or seg.name):
            resp = await bot.adapter.request(Request("GET", seg.url))
            return ms.attachment(
                seg.id or seg.name,
                content=resp.content,  # type: ignore
            )
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.reference(seg.origin or int(seg.id), fail_if_not_exists=False)

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.discord import Bot as DiscordBot

        assert isinstance(bot, DiscordBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())
        return await bot.send_to(channel_id=int(target.id), message=message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        from nonebot.adapters.discord.api.model import MessageGet
        from nonebot.adapters.discord.bot import Bot as DiscordBot

        _mid: MessageGet = cast(MessageGet, mid)

        assert isinstance(bot, DiscordBot)

        return await bot.delete_message(channel_id=mid.channel_id, message_id=_mid.id)

    async def edit(self, new: Message, mid: Any, bot: Bot, context: Union[Target, Event]):
        from nonebot.adapters.discord.api.model import MessageGet
        from nonebot.adapters.discord.bot import Bot as DiscordBot
        from nonebot.adapters.discord.message import parse_message

        _mid: MessageGet = cast(MessageGet, mid)

        assert isinstance(bot, DiscordBot)
        if TYPE_CHECKING:
            assert isinstance(new, self.get_message_type())

        return await bot.edit_message(channel_id=mid.channel_id, message_id=_mid.id, **parse_message(new))
