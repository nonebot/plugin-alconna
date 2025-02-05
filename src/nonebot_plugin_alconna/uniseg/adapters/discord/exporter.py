from pathlib import Path
from typing import TYPE_CHECKING, Any, Union, cast

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.internal.driver import Request
from nonebot.adapters.discord.bot import Bot as DiscordBot
from nonebot.adapters.discord.api.model import Button as ButtonModel
from nonebot.adapters.discord.message import Message, MessageSegment, parse_message
from nonebot.adapters.discord.api.types import ButtonStyle, ChannelType, TextInputStyle
from nonebot.adapters.discord.api.model import Channel, ActionRow, TextInput, MessageGet
from nonebot.adapters.discord.event import MessageEvent, GuildMessageCreateEvent, DirectMessageCreateEvent

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
    Button,
    Keyboard,
)


class DiscordMessageExporter(MessageExporter[Message]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.discord

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.message_id)

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if isinstance(event, MessageEvent):
            if isinstance(event, GuildMessageCreateEvent):
                return Target(
                    str(event.channel_id),
                    str(event.guild_id),
                    channel=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    scope=SupportScope.discord,
                )
            if isinstance(event, DirectMessageCreateEvent):
                return Target(
                    str(event.channel_id),
                    channel=True,
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    scope=SupportScope.discord,
                )
            return Target(
                str(event.channel_id),
                channel=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.discord,
            )
        if isinstance(event, Channel):
            return Target(
                str(event.id),
                channel=True,
                private=event.type == ChannelType.DM,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.discord,
            )
        raise NotImplementedError

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag == "role":
            return MessageSegment.mention_role(int(seg.target))
        if seg.flag == "channel":
            return MessageSegment.mention_channel(int(seg.target))
        return MessageSegment.mention_user(int(seg.target))

    @export
    async def at_all(self, seg: AtAll, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.mention_everyone()

    @export
    async def emoji(self, seg: Emoji, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.custom_emoji(seg.name or "", seg.id)

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Union[Bot, None]) -> "MessageSegment":
        name = seg.__class__.__name__.lower()

        if seg.raw and (seg.id or seg.name):
            content = seg.raw_bytes
            return MessageSegment.attachment(seg.id or seg.name, content=content)
        if seg.path:
            path = Path(seg.path)
            return MessageSegment.attachment(path.name, content=path.read_bytes())
        if bot and seg.url and (seg.id or seg.name):
            resp = await bot.adapter.request(Request("GET", seg.url))
            return MessageSegment.attachment(
                seg.id or seg.name,
                content=resp.content,  # type: ignore
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.reference(seg.origin or int(seg.id), fail_if_not_exists=False)

    def _button(self, seg: Button, bot: Union[Bot, None]):
        styles = {
            "primary": ButtonStyle.Primary,
            "secondary": ButtonStyle.Secondary,
            "success": ButtonStyle.Success,
            "danger": ButtonStyle.Danger,
            "link": ButtonStyle.Link,
        }
        label = str(seg.label)
        if seg.flag == "link" and seg.url:
            return ButtonModel(style=styles.get(seg.style or "", ButtonStyle.Primary), label=label, url=seg.url)
        if seg.flag == "action":
            return ButtonModel(
                style=styles.get(seg.style or "", ButtonStyle.Primary), label=label, custom_id=seg.id or label
            )
        if seg.text:
            return TextInput(
                custom_id=seg.id or label,
                style=TextInputStyle.Short,
                label=label,
                placeholder=seg.clicked_label or label,
                value=seg.text,
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="button", seg=seg))

    @export
    async def button(self, seg: Button, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.component(self._button(seg, bot))

    @export  # type: ignore
    async def keyboard(self, seg: Keyboard, bot: Union[Bot, None]):
        if not seg.children:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="keyboard", seg=seg))

        if not seg.row:
            return MessageSegment.component(ActionRow(components=[self._button(but, bot) for but in seg.children]))

        buttons = [self._button(but, bot) for but in seg.children]
        return [
            MessageSegment.component(ActionRow(components=buttons[i : i + seg.row]))  # type: ignore
            for i in range(0, len(buttons), seg.row)
        ]

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, DiscordBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, Event):
            return await bot.send(target, message, **kwargs)  # type: ignore
        if target.private:
            dm = await bot.create_DM(recipient_id=int(target.id))
            return await bot.send_to(channel_id=dm.id, message=message, **kwargs)
        return await bot.send_to(channel_id=int(target.id), message=message, **kwargs)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        _mid: MessageGet = cast(MessageGet, mid)
        assert isinstance(bot, DiscordBot)
        return await bot.delete_message(channel_id=mid.channel_id, message_id=_mid.id)

    async def edit(self, new: Message, mid: Any, bot: Bot, context: Union[Target, Event]):
        _mid: MessageGet = cast(MessageGet, mid)
        assert isinstance(bot, DiscordBot)
        if TYPE_CHECKING:
            assert isinstance(new, self.get_message_type())
        return await bot.edit_message(channel_id=mid.channel_id, message_id=_mid.id, **parse_message(new))

    def get_reply(self, mid: Any):
        _mid: MessageGet = cast(MessageGet, mid)
        return Reply(str(_mid.id), origin=_mid.id)
