from nonebot.adapters import Bot, Event
from nonebot_adapter_tailchat.message import MessageSegment
from nonebot_adapter_tailchat.event import DefaultMessageEvent

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import At, File, Text, Emoji, Image, Reply

STYLE_TYPE_MAP = {
    "b": "bold",
    "strong": "bold",
    "bold": "bold",
    "i": "italic",
    "em": "italic",
    "italic": "italic",
    "u": "underline",
    "ins": "underline",
    "underline": "underline",
    "s": "strikethrough",
    "del": "strikethrough",
    "strike": "strikethrough",
    "strikethrough": "strikethrough",
    "spl": "spoiler",
    "spoiler": "spoiler",
    "code": "code",
    "sup": "superscript",
    "superscript": "superscript",
    "sub": "subscript",
    "subscript": "subscript",
    "p": "paragraph",
    "paragraph": "paragraph",
}


class TailChatMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.tail_chat

    @build("text")
    def text(self, seg: MessageSegment):
        return Text(seg.data["text"])

    @build("b")
    def b(self, seg: MessageSegment):
        return Text(seg.data["text"]).bold()

    @build("i")
    def i(self, seg: MessageSegment):
        return Text(seg.data["text"]).italic()

    @build("u")
    def u(self, seg: MessageSegment):
        return Text(seg.data["text"]).underline()

    @build("s")
    def s(self, seg: MessageSegment):
        return Text(seg.data["text"]).strikethrough()

    @build("rich")
    def rich(self, seg: MessageSegment):
        tags = [t.__name__ for t in seg.tags]
        return Text(seg.data["text"]).mark(0, len(seg.data["text"]), *[STYLE_TYPE_MAP.get(t, t) for t in tags])

    @build("url")
    def url(self, seg: MessageSegment):
        _url = seg.data["extra"]["url"]
        if _url.startswith("/main/group/"):
            return At("channel", _url[12:], seg.data["text"])
        text = Text(_url).link()
        text._children = [Text(seg.data["text"])]
        return text

    @build("code")
    def code(self, seg: MessageSegment):
        return Text(seg.data["text"]).code()

    @build("markdown")
    def markdown(self, seg: MessageSegment):
        return Text(seg.data["text"]).markdown()

    @build("at")
    def at(self, seg: MessageSegment):
        return At("user", seg.data["extra"]["at"], seg.data["text"])

    @build("emoji")
    def emoji(self, seg: MessageSegment):
        return Emoji(seg.data["text"], seg.data["text"])

    @build("img")
    def img(self, seg: MessageSegment):
        return Image(url=seg.data["text"])

    @build("file")
    def file(self, seg: MessageSegment):
        return File(url=seg.data["extra"]["url"], name=seg.data["text"])

    async def extract_reply(self, event: Event, bot: Bot):
        if isinstance(event, DefaultMessageEvent) and event.reply:
            return Reply(event.reply.id, event.reply.content, event.reply)
