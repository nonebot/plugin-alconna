from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.qq.bot import Bot as QQBot
from nonebot.adapters.qq.message import Message, MessageSegment
from nonebot.adapters.qq.models.guild import Message as GuildMessage
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
from nonebot_plugin_alconna.uniseg.segment import At, File, Text, AtAll, Audio, Emoji, Image, Reply, Video, Voice
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export


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
                )
            elif event.channel_id:
                return Target(
                    event.channel_id,
                    event.guild_id or "",
                    channel=True,
                    source=str(event.id),
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    scope=SupportScope.qq_api,
                )
            else:
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
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        if seg.extract_most_style() == "markdown":
            return MessageSegment.markdown(seg.text)
        elif seg.styles:
            return MessageSegment.markdown(str(seg))
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        if seg.flag == "channel":
            return MessageSegment.mention_channel(seg.target)
        elif seg.flag == "user":
            return MessageSegment.mention_user(seg.target)
        else:
            raise SerializeFailed(
                lang.require("nbp-uniseg", "failed_segment").format(adapter="qq", seg=seg, target="mention")
            )

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        return MessageSegment.mention_everyone()

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        return MessageSegment.emoji(seg.id)

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Bot) -> "MessageSegment":
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
        elif seg.path:
            return file_method(Path(seg.path))
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        return MessageSegment.reference(seg.id)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        assert isinstance(bot, QQBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, Event):
            assert isinstance(target, MessageEvent)
            return await bot.send(
                event=target,
                message=message,
            )

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
                )
            return await bot.send_to_channel(
                channel_id=target.id,
                message=message,
                msg_id=target.source,
            )
        if target.private:
            res = await bot.send_to_c2c(
                openid=target.id,
                message=message,
                msg_id=target.source,
            )
        else:
            res = await bot.send_to_group(
                group_openid=target.id,
                message=message,
                msg_id=target.source,
            )
        target.extra["qq.reply_seq"] += 1
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
        return

    def get_reply(self, mid: Any):
        if isinstance(mid, GuildMessage):
            return Reply(mid.id)
        raise NotImplementedError
