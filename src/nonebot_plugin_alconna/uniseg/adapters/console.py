from typing import TYPE_CHECKING

from nonebot.adapters import Bot

from ..segment import Text, Emoji
from ..export import MessageExporter, export

if TYPE_CHECKING:
    from nonebot.adapters.console.message import MessageSegment


class ConsoleMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.onebot.v11.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "Console"

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if seg.style.startswith("markup"):
            _style = seg.style.split(":", 1)[-1]
            return ms.markup(seg.text, _style)
        if seg.style.startswith("markdown"):
            code_theme = seg.style.split(":", 1)[-1]
            return ms.markdown(seg.text, code_theme)
        return ms.text(seg.text)

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.emoji(seg.name or seg.id)
