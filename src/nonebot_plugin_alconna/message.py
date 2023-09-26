from nonebot.adapters import Message, MessageSegment


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
