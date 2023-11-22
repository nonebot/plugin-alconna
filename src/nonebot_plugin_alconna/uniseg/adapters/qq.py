from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from tarina import lang
from nonebot.adapters import Bot, Event, Message

from ..export import Target, MessageExporter, SerializeFailed, export
from ..segment import At, File, Text, AtAll, Audio, Emoji, Image, Reply, Video, Voice

if TYPE_CHECKING:
    from nonebot.adapters.qq.message import MessageSegment


class QQMessageExporter(MessageExporter["MessageSegment"]):
    @classmethod
    def get_adapter(cls) -> str:
        return "QQ"

    def get_message_type(self):
        from nonebot.adapters.qq.message import Message

        return Message

    def get_target(self, event: Event) -> Target:
        from nonebot.adapters.qq.event import (
            ForumEvent,
            GuildEvent,
            ChannelEvent,
            GroupRobotEvent,
            FriendRobotEvent,
            GuildMemberEvent,
            GuildMessageEvent,
            MessageAuditEvent,
            MessageReactionEvent,
            C2CMessageCreateEvent,
            InteractionCreateEvent,
            GroupAtMessageCreateEvent,
        )

        if isinstance(event, GuildMessageEvent):
            if event.__type__.value.startswith("DIRECT"):
                return Target(str(event.author.id), str(event.guild_id), channel=True, private=True, source=str(event.id))  # type: ignore  # noqa: E501
            return Target(str(event.channel_id), str(event.guild_id), channel=True, source=str(event.id))
        if isinstance(event, GuildEvent):
            return Target(str(event.id), channel=True)
        if isinstance(event, GuildMemberEvent):
            return Target(str(event.user.id), str(event.guild_id), channel=True)  # type: ignore
        if isinstance(event, ChannelEvent):
            return Target(str(event.id), str(event.guild_id), channel=True)
        if isinstance(event, MessageAuditEvent):
            return Target(str(event.channel_id), str(event.guild_id), channel=True)
        if isinstance(event, MessageReactionEvent):
            return Target(str(event.channel_id), str(event.guild_id), channel=True)
        if isinstance(event, ForumEvent):
            return Target(str(event.channel_id), str(event.guild_id), channel=True)
        if isinstance(event, C2CMessageCreateEvent):
            return Target(str(event.author.id), private=True, source=str(event.id))  # type: ignore
        if isinstance(event, GroupAtMessageCreateEvent):
            return Target(event.group_id, source=str(event.id))  # type: ignore
        if isinstance(event, InteractionCreateEvent):
            if event.group_open_id:
                return Target(event.group_open_id, source=str(event.id))
            elif event.channel_id:
                return Target(event.channel_id, event.guild_id or "", channel=True, source=str(event.id))
            else:
                return Target(event.get_user_id(), private=True, source=str(event.id))
        if isinstance(event, FriendRobotEvent):
            return Target(event.open_id, private=True)
        if isinstance(event, GroupRobotEvent):
            return Target(event.group_openid)
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.qq.event import (
            GuildMessageEvent,
            C2CMessageCreateEvent,
            InteractionCreateEvent,
            GroupAtMessageCreateEvent,
        )

        assert isinstance(
            event,
            (InteractionCreateEvent, GuildMessageEvent, C2CMessageCreateEvent, GroupAtMessageCreateEvent),
        )
        return str(event.id)

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.style == "markdown":
            return ms.markdown(seg.text)
        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.flag == "channel":
            return ms.mention_channel(seg.target)
        elif seg.flag == "user":
            return ms.mention_user(seg.target)
        else:
            raise SerializeFailed(
                lang.require("nbp-uniseg", "failed_segment").format(adapter="qq", seg=seg, target="mention")
            )

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.mention_everyone()

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.emoji(seg.id)

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        name = seg.__class__.__name__.lower()
        method = {
            "image": ms.image,
            "voice": ms.audio,
            "video": ms.video,
            "audio": ms.audio,
            "file": ms.file,
        }[name]

        file_method = {
            "image": ms.file_image,
            "voice": ms.file_audio,
            "video": ms.file_video,
            "audio": ms.file_audio,
            "file": ms.file_file,
        }[name]

        if seg.url:
            return method(seg.url)
        elif seg.raw:
            return file_method(seg.raw_bytes)
        elif seg.path:
            return file_method(Path(seg.path))
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.reference(seg.id)

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.qq.bot import Bot as QQBot

        assert isinstance(bot, QQBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

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
            return await bot.send_to_c2c(
                user_id=target.id,
                message=message,
                msg_id=target.source,
            )
        return await bot.send_to_group(
            group_id=target.id,
            message=message,
            msg_id=target.source,
        )

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        from nonebot.adapters.qq.bot import Bot as QQBot
        from nonebot.adapters.qq.event import DirectMessageCreateEvent
        from nonebot.adapters.qq.models.guild import Message as GuildMessage

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
