from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event, Message

from ..segment import At, Text, Image
from ..export import Target, MessageExporter, export

if TYPE_CHECKING:
    from nonebot.adapters.github.message import MessageSegment  # type: ignore


class GithubMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.github.message import Message  # type: ignore

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "GitHub"

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.github.event import MessageEvent  # type: ignore

        assert isinstance(event, MessageEvent)
        return str(event.id)  # type: ignore

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.text(f"@{seg.target}")

    @export
    async def image(self, seg: Image, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        assert seg.url, "github image segment must have url"
        return ms.text(f"![]({seg.url})")

    async def send_to(self, target: Target, bot: Bot, message: Message):
        raise NotImplementedError
