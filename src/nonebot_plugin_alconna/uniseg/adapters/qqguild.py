from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from tarina import lang
from nonebot.adapters import Bot, Event, Message

from ..segment import At, Text, AtAll, Emoji, Image, Reply
from ..export import Target, MessageExporter, SerializeFailed, export

if TYPE_CHECKING:
    from nonebot.adapters.qqguild.message import MessageSegment


class QQGuildMessageExporter(MessageExporter["MessageSegment"]):
    @classmethod
    def get_adapter(cls) -> str:
        return "QQ Guild"

    def get_message_type(self):
        from nonebot.adapters.qqguild.message import Message

        return Message

    def get_target(self, event: Event) -> Target:
        from nonebot.adapters.qqguild.event import (
            ForumEvent,
            GuildEvent,
            ChannelEvent,
            MessageEvent,
            GuildMemberEvent,
            MessageAuditEvent,
            MessageReactionEvent,
        )

        if isinstance(event, MessageEvent):
            if event.__type__.value.startswith("DIRECT"):
                return Target(str(event.author.id), str(event.guild_id), channel=True, private=True, source=str(event.id))  # type: ignore  # noqa: E501
            return Target(str(event.channel_id), str(event.guild_id), channel=True, source=str(event.id))
        elif isinstance(event, GuildEvent):
            return Target(str(event.id), channel=True)
        elif isinstance(event, GuildMemberEvent):
            return Target(str(event.user.id), str(event.guild_id), channel=True)  # type: ignore
        elif isinstance(event, ChannelEvent):
            return Target(str(event.id), str(event.guild_id), channel=True)
        elif isinstance(event, MessageAuditEvent):
            return Target(str(event.channel_id), str(event.guild_id), channel=True)
        elif isinstance(event, MessageReactionEvent):
            return Target(str(event.channel_id), str(event.guild_id), channel=True)
        elif isinstance(event, ForumEvent):
            return Target(str(event.channel_id), str(event.guild_id), channel=True)
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.qqguild.event import MessageEvent

        assert isinstance(event, MessageEvent)
        return str(event.id)

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.flag == "channel":
            return ms.mention_channel(int(seg.target))
        elif seg.flag == "user":
            return ms.mention_user(int(seg.target))
        else:
            raise SerializeFailed(
                lang.require("nbp-uniseg", "failed_segment").format(
                    adapter="qqguild", seg=seg, target="mention"
                )
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
    async def image(self, seg: Image, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.url:
            return ms.image(seg.url)
        elif seg.raw:
            return ms.file_image(seg.raw_bytes)
        elif seg.path:
            return ms.file_image(Path(seg.path))
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.reference(seg.id)

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.qqguild.bot import Bot as QQBot

        assert isinstance(bot, QQBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if target.private:
            if not target.parent_id:
                raise NotImplementedError
            dms = await bot.post_dms(recipient_id=target.id, source_guild_id=target.parent_id)
            # 私信需要使用 post_dms_messages
            # https://bot.q.qq.com/wiki/develop/api/openapi/dms/post_dms_messages.html#%E5%8F%91%E9%80%81%E7%A7%81%E4%BF%A1
            return await bot.send_to_dms(
                guild_id=dms.guild_id,  # type: ignore
                message=message,
                msg_id=int(target.source),
            )
        return await bot.send_to_channel(
            channel_id=target.id,
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
