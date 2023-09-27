from nonebot.adapters import Bot, MessageSegment

from ..segment import Text
from ..export import MessageExporter, export


class BilibiliMessageExporter(MessageExporter):
    def get_message_type(self):
        from nonebot.adapters.bilibili.message import Message  # type: ignore

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "BilibiliLive"

    @export
    async def text(self, seg: Text, bot: Bot) -> MessageSegment:
        msg = self.get_message_type()
        ms = msg.get_segment_class()

        return ms.danmu(seg.text)
