from pathlib import Path
from dataclasses import dataclass
from typing_extensions import override
from typing import TYPE_CHECKING, Any, Union

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.qq.bot import Bot as QQBot
from nonebot.adapters.qq.models.common import Action
from nonebot.adapters.qq.message import Message, MessageSegment
from nonebot.adapters.qq.models.common import Button as ButtonModel
from nonebot.adapters.qq.models.guild import Message as GuildMessage
from nonebot.adapters.qq.models import PostC2CMessagesReturn, PostGroupMessagesReturn
from nonebot.adapters.qq.models.common import Permission, RenderData, InlineKeyboard, MessageKeyboard, InlineKeyboardRow
from nonebot.adapters.qq.event import (
    ForumEvent,
    GuildEvent,
    ChannelEvent,
    MessageEvent,
    GroupRobotEvent,
    FriendRobotEvent,
    GuildMemberEvent,
    GuildMessageEvent,
    MessageAuditEvent,
    MessageReactionEvent,
    C2CMessageCreateEvent,
    InteractionCreateEvent,
    DirectMessageCreateEvent,
    GroupAtMessageCreateEvent,
)

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


@dataclass
class ButtonSegment(MessageSegment):
    @override
    def __str__(self) -> str:
        return "<$qq.button>"


@dataclass
class ButtonRowSegment(MessageSegment):
    @override
    def __str__(self) -> str:
        return "<$qq.button_row>"


class QQMessageExporter(MessageExporter[Message]):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.qq

    def get_message_type(self):
        return Message

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if isinstance(event, GuildMessageEvent):
            if event.__type__.value.startswith("DIRECT"):
                return Target(
                    str(event.author.id),
                    str(event.guild_id),
                    channel=True,
                    private=True,
                    source=str(event.id),
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    scope=SupportScope.qq_api,
                )  # noqa: E501
            return Target(
                str(event.channel_id),
                str(event.guild_id),
                channel=True,
                source=str(event.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_api,
            )
        if isinstance(event, GuildEvent):
            return Target(
                str(event.id),
                channel=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_api,
            )
        if isinstance(event, GuildMemberEvent):
            return Target(
                str(event.user.id),  # type: ignore
                str(event.guild_id),
                channel=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_api,
            )
        if isinstance(event, ChannelEvent):
            return Target(
                str(event.id),
                str(event.guild_id),
                channel=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_api,
            )
        if isinstance(event, MessageAuditEvent):
            return Target(
                str(event.channel_id),
                str(event.guild_id),
                channel=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_api,
            )
        if isinstance(event, MessageReactionEvent):
            return Target(
                str(event.channel_id),
                str(event.guild_id),
                channel=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_api,
            )
        if isinstance(event, ForumEvent):
            return Target(
                str(event.channel_id),
                str(event.guild_id),
                channel=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_api,
            )
        if isinstance(event, C2CMessageCreateEvent):
            return Target(
                str(event.author.id),
                private=True,
                source=str(event.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                extra={"qq.reply_seq": event._reply_seq},
                scope=SupportScope.qq_api,
            )
        if isinstance(event, GroupAtMessageCreateEvent):
            return Target(
                event.group_openid,
                source=str(event.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                extra={"qq.reply_seq": event._reply_seq},
                scope=SupportScope.qq_api,
            )
        if isinstance(event, InteractionCreateEvent):
            if event.group_openid:
                return Target(
                    event.group_openid,
                    source=str(event.id),
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    scope=SupportScope.qq_api,
                    extra={"qq.interaction": True},
                )
            if event.channel_id:
                return Target(
                    event.channel_id,
                    event.guild_id or "",
                    channel=True,
                    source=str(event.id),
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    scope=SupportScope.qq_api,
                )
            return Target(
                event.get_user_id(),
                private=True,
                source=str(event.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_api,
            )
        if isinstance(event, FriendRobotEvent):
            return Target(
                event.openid,
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_api,
            )
        if isinstance(event, GroupRobotEvent):
            return Target(
                event.group_openid,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_api,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        assert isinstance(
            event,
            (InteractionCreateEvent, GuildMessageEvent, C2CMessageCreateEvent, GroupAtMessageCreateEvent),
        )
        return str(event.id)

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.extract_most_style() == "markdown":
            return MessageSegment.markdown(seg.text)
        if seg.styles:
            return MessageSegment.markdown(str(seg))
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag == "channel":
            return MessageSegment.mention_channel(seg.target)
        if seg.flag == "user":
            return MessageSegment.mention_user(seg.target)
        raise SerializeFailed(
            lang.require("nbp-uniseg", "failed_segment").format(adapter="qq", seg=seg, target="mention")
        )

    @export
    async def at_all(self, seg: AtAll, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.mention_everyone()

    @export
    async def emoji(self, seg: Emoji, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.emoji(seg.id)

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Union[Bot, None]) -> "MessageSegment":
        name = seg.__class__.__name__.lower()
        method = {
            "image": MessageSegment.image,
            "voice": MessageSegment.audio,
            "video": MessageSegment.video,
            "audio": MessageSegment.audio,
            "file": MessageSegment.file,
        }[name]

        if seg.url:
            return method(seg.url)
        if seg.__class__.to_url and seg.raw:
            return method(
                await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name)
            )
        if seg.__class__.to_url and seg.path:
            return method(
                await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name)
            )

        file_method = {
            "image": MessageSegment.file_image,
            "voice": MessageSegment.file_audio,
            "video": MessageSegment.file_video,
            "audio": MessageSegment.file_audio,
            "file": MessageSegment.file_file,
        }[name]
        if seg.raw:
            return file_method(seg.raw_bytes)
        if seg.path:
            return file_method(Path(seg.path))
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.reference(seg.id)

    def _button(self, seg: Button, bot: Union[Bot, None]):
        if seg.permission == "all":
            perm = Permission(type=2)
        elif seg.permission == "admin":
            perm = Permission(type=1)
        elif seg.permission[0].flag == "role":
            perm = Permission(type=3, specify_role_ids=[i.target for i in seg.permission])
        else:
            perm = Permission(type=0, specify_user_ids=[i.target for i in seg.permission])
        label = str(seg.label)
        return ButtonModel(
            id=seg.id or (label if seg.flag == "action" else None),
            render_data=RenderData(
                label=label,
                visited_label=seg.clicked_label or label,
                style=0 if seg.style == "secondary" else 1,
            ),
            action=Action(
                type=0 if seg.flag == "link" else 1 if seg.flag == "action" else 2,
                data=seg.text or seg.url or (label if seg.flag != "action" else None),
                enter=True if seg.flag == "enter" else False if seg.flag == "input" else None,
                unsupport_tips="该版本暂不支持查看此消息，请升级至最新版本。",
                permission=perm,
            ),
        )

    @export
    async def button(self, seg: Button, bot: Union[Bot, None]):
        return ButtonSegment("$qq:button", {"button": self._button(seg, bot)})

    @export
    async def keyboard(self, seg: Keyboard, bot: Union[Bot, None]):
        if not seg.children:
            if not seg.id:
                raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="keyboard", seg=seg))
            return MessageSegment.keyboard(MessageKeyboard(id=seg.id))
        if len(seg.children) > 25:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="keyboard", seg=seg))
        buttons = [self._button(child, bot) for child in seg.children]
        if len(buttons) < 6 and not seg.row:
            return ButtonRowSegment("$qq:button_row", {"buttons": buttons})
        rows = [
            InlineKeyboardRow(buttons=buttons[i : i + (seg.row or 5)]) for i in range(0, len(buttons), seg.row or 5)
        ]
        return MessageSegment.keyboard(MessageKeyboard(content=InlineKeyboard(rows=rows)))

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, QQBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        kb = None
        if message.has("$qq:button"):
            buttons = [seg.data["button"] for seg in message.get("$qq:button")]
            message = message.exclude("$qq:button")
            rows = [InlineKeyboardRow(buttons=buttons[i : i + 5]) for i in range(0, len(buttons), 5)]
            kb = MessageKeyboard(content=InlineKeyboard(rows=rows))

        if message.has("$qq:button_row"):
            rows = [InlineKeyboardRow(buttons=seg.data["buttons"]) for seg in message.get("$qq:button_row")]
            message = message.exclude("$qq:button_row")
            if not kb:
                kb = MessageKeyboard(content=InlineKeyboard(rows=rows))
            else:
                assert kb.content
                assert kb.content.rows
                kb.content.rows += rows
        if kb:
            message.append(MessageSegment.keyboard(kb))

        if isinstance(target, Event):
            assert isinstance(target, MessageEvent)
            if isinstance(target, (C2CMessageCreateEvent, GroupAtMessageCreateEvent)):
                message = message.exclude("mention_channel", "mention_user", "mention_everyone", "reference")
            return await bot.send(event=target, message=message, **kwargs)

        if target.extra.get("qq.reply_seq") is not None:
            target.extra["qq.reply_seq"] += 1

        if target.channel:
            if target.private:
                if not target.parent_id:
                    raise NotImplementedError
                dms = await bot.post_dms(recipient_id=target.id, source_guild_id=target.parent_id)
                # 私信需要使用 post_dms_messages
                # https://bot.q.qq.com/wiki/develop/api/openapi/dms/post_dms_messages.html#%E5%8F%91%E9%80%81%E7%A7%81%E4%BF%A1
                return await bot.send_to_dms(
                    guild_id=dms.guild_id,  # type: ignore
                    message=message,
                    msg_id=target.source,
                    **kwargs,  # type: ignore
                )
            return await bot.send_to_channel(channel_id=target.id, message=message, msg_id=target.source, **kwargs)
        message = message.exclude("mention_channel", "mention_user", "mention_everyone", "reference")
        if target.private:
            res = await bot.send_to_c2c(
                openid=target.id,
                message=message,
                msg_id=target.source,
                msg_seq=target.extra.get("qq.reply_seq"),
                **kwargs,
            )
        elif target.extra.get("qq.interaction", False):
            return await bot.send_to_group(group_openid=target.id, message=message, event_id=target.source, **kwargs)
        else:
            res = await bot.send_to_group(
                group_openid=target.id,
                message=message,
                msg_id=target.source,
                msg_seq=target.extra.get("qq.reply_seq"),
                **kwargs,
            )
        return res

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, QQBot)
        if isinstance(mid, GuildMessage):
            if isinstance(context, Target):
                if context.private:
                    await bot.delete_dms_message(
                        guild_id=mid.guild_id,
                        message_id=mid.id,
                    )
                else:
                    await bot.delete_message(
                        channel_id=mid.channel_id,
                        message_id=mid.id,
                    )
            elif isinstance(context, DirectMessageCreateEvent):
                await bot.delete_dms_message(
                    guild_id=mid.guild_id,
                    message_id=mid.id,
                )
            else:
                await bot.delete_message(
                    channel_id=mid.channel_id,
                    message_id=mid.id,
                )
        elif isinstance(mid, PostGroupMessagesReturn):
            if isinstance(context, Target):
                if not context.private:
                    await bot.delete_group_message(
                        group_openid=context.id,
                        message_id=mid.id,  # type: ignore
                    )
            elif isinstance(context, GroupAtMessageCreateEvent):
                await bot.delete_group_message(
                    group_openid=context.group_openid,
                    message_id=mid.id,  # type: ignore
                )
        elif isinstance(mid, PostC2CMessagesReturn):
            if isinstance(context, Target):
                if context.private:
                    await bot.delete_c2c_message(
                        openid=context.id,
                        message_id=mid.id,  # type: ignore
                    )
            elif isinstance(context, C2CMessageCreateEvent):
                await bot.delete_c2c_message(
                    openid=context.author.id,
                    message_id=mid.id,  # type: ignore
                )

    def get_reply(self, mid: Any):
        if isinstance(mid, GuildMessage):
            return Reply(mid.id)
        raise NotImplementedError
