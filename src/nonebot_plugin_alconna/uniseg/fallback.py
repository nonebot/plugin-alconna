from enum import Enum

from nonebot.adapters import Message, MessageSegment


class FallbackStrategy(str, Enum):
    ignore = "ignore"
    """将丢弃未转换元素"""

    text = "text"
    """将未转换元素作为文本元素"""

    rollback = "rollback"
    """从未转换元素的子元素中提取可能的可发送元素"""

    forbid = "forbid"
    """禁止未转换元素"""


class FallbackSegment(MessageSegment["FallbackMessage"]):
    @classmethod
    def get_message_class(cls):
        return FallbackMessage

    def __str__(self) -> str:
        if self.type == "text":
            return self.data["text"]
        return f"[{self.type}][{self.data}]"

    def is_text(self) -> bool:
        return self.type == "text"

    @staticmethod
    def text(text: str) -> "FallbackSegment":
        return FallbackSegment("text", {"text": text})


class FallbackMessage(Message[FallbackSegment]):
    @classmethod
    def get_segment_class(cls):
        return FallbackSegment

    @staticmethod
    def _construct(msg: str):
        yield FallbackSegment.text(msg)
