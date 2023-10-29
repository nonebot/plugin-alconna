from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from tarina import lang
from nonebot.adapters import Bot, Event, Message

from ..segment import At, Text, AtAll, Emoji, Image, Reply
from ..export import Target, MessageExporter, SerializeFailed, export

if TYPE_CHECKING:
    from nonebot.adapters.qq.message import MessageSegment


class QQMessageExporter(MessageExporter["MessageSegment"]):
    @classmethod
    def get_adapter(cls) -> str:
        return "QQ"

    def get_message_type(self):
        from nonebot.adapters.qq.message import Message

        return Message

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.style == "markdown":
            return ms.markdown(seg.text)
        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.target == "channel":
            return ms.mention_channel(int(seg.target))
        elif seg.target == "user":
            return ms.mention_user(int(seg.target))
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
    async def image(self, seg: Image, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.url:
            return ms.image(seg.url)
        elif seg.raw or seg.path:
            return ms.file_image(seg.raw_bytes or Path(seg.path))
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.reference(seg.id)

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.qq.bot import Bot as QQBot

        assert isinstance(bot, QQBot)

        if target.channel:
            if target.private:
                if not target.parent_id:
                    raise NotImplementedError
                dms = await bot.post_dms(target.id, target.parent_id)
                # 私信需要使用 post_dms_messages
                # https://bot.q.qq.com/wiki/develop/api/openapi/dms/post_dms_messages.html#%E5%8F%91%E9%80%81%E7%A7%81%E4%BF%A1
                return await bot.send_to_dms(
                    guild_id=dms.guild_id,
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
