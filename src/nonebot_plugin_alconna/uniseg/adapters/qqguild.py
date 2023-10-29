from pathlib import Path
from typing import TYPE_CHECKING

from tarina import lang
from nonebot.adapters import Bot, Message

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

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

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
        elif seg.raw or seg.path:
            return ms.file_image(seg.raw_bytes or Path(seg.path))
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.reference(seg.id)

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.qqguild.bot import Bot as QQBot

        assert isinstance(bot, QQBot)

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
        return await bot.send_to(
            channel_id=target.id,
            message=message,
            msg_id=target.source,
        )
