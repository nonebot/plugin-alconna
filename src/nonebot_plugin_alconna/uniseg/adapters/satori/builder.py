from pathlib import Path
from base64 import b64decode
from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.satori.message import Message
from nonebot.adapters.satori.event import MessageEvent
from nonebot.adapters.satori.message import MessageSegment
from nonebot.adapters.satori.message import At as AtSegment
from nonebot.adapters.satori.message import File as FileSegment
from nonebot.adapters.satori.message import Link as LinkSegment
from nonebot.adapters.satori.message import Text as TextSegment
from nonebot.adapters.satori.message import Audio as AudioSegment
from nonebot.adapters.satori.message import Image as ImageSegment
from nonebot.adapters.satori.message import Sharp as SharpSegment
from nonebot.adapters.satori.message import Video as VideoSegment
from nonebot.adapters.satori.message import RenderMessage as RenderMessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import At, File, Text, AtAll, Audio, Image, Other, Reply, Video, Reference

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


class SatoriMessageBuilder(MessageBuilder[MessageSegment]):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.satori

    def wildcard_build(self, seg: MessageSegment):
        children = seg._children
        seg._children = Message()
        return Other(seg)(*self.generate(children))

    @build("text")
    def text(self, seg: TextSegment):
        styles = {scale: [STYLE_TYPE_MAP.get(s, s) for s in _styles] for scale, _styles in seg.data["styles"].items()}
        return Text(seg.data["text"], styles)(*(self.generate(seg.children)))

    @build("at")
    def at(self, seg: AtSegment):
        if "type" in seg.data and seg.data["type"] in ("all", "here"):
            return AtAll(here=seg.data["type"] == "here")(*self.generate(seg.children))
        if "id" in seg.data:
            return At("user", seg.data["id"], seg.data.get("name"))(*self.generate(seg.children))
        if "role" in seg.data:
            return At("role", seg.data["role"], seg.data.get("name"))(*self.generate(seg.children))

    @build("sharp")
    def sharp(self, seg: SharpSegment):
        return At("channel", seg.data["id"], seg.data.get("name"))(*self.generate(seg.children))

    @build("link")
    def link(self, seg: LinkSegment):
        display = seg.data.get("display")
        text = Text(seg.data["text"]).mark(0, len(seg.data["text"]), "link")
        if display:
            text._children = [Text(display)]
        return text(*self.generate(seg.children))

    @build("img", "image")
    def image(self, seg: ImageSegment):
        src = seg.data["src"]
        if src.startswith("http"):
            return Image(url=src)(*self.generate(seg.children))
        if src.startswith("file://"):
            return Image(path=Path(src[7:]))(*self.generate(seg.children))
        if src.startswith("data:"):
            mime, b64 = src[5:].split(";", 1)
            return Image(raw=b64decode(b64[7:]), mimetype=mime)(*self.generate(seg.children))
        return Image(seg.data["src"])(*self.generate(seg.children))

    @build("audio")
    def audio(self, seg: AudioSegment):
        src = seg.data["src"]
        if src.startswith("http"):
            return Audio(url=src)(*self.generate(seg.children))
        if src.startswith("file://"):
            return Audio(path=Path(src[7:]))(*self.generate(seg.children))
        if src.startswith("data:"):
            mime, b64 = src[5:].split(";", 1)
            return Audio(raw=b64decode(b64[7:]), mimetype=mime)(*self.generate(seg.children))
        return Audio(seg.data["src"])(*self.generate(seg.children))

    @build("video")
    def video(self, seg: VideoSegment):
        src = seg.data["src"]
        if src.startswith("http"):
            return Video(url=src)(*self.generate(seg.children))
        if src.startswith("file://"):
            return Video(path=Path(src[7:]))(*self.generate(seg.children))
        if src.startswith("data:"):
            mime, b64 = src[5:].split(";", 1)
            return Video(raw=b64decode(b64[7:]), mimetype=mime)(*self.generate(seg.children))
        return Video(seg.data["src"])(*self.generate(seg.children))

    @build("file")
    def file(self, seg: FileSegment):
        src = seg.data["src"]
        if src.startswith("http"):
            return File(url=src)(*self.generate(seg.children))
        if src.startswith("file://"):
            return File(path=Path(src[7:]))(*self.generate(seg.children))
        if src.startswith("data:"):
            mime, b64 = src[5:].split(";", 1)
            return File(raw=b64decode(b64[7:]), mimetype=mime)(*self.generate(seg.children))
        return File(seg.data["src"])(*self.generate(seg.children))

    @build("quote")
    def quote(self, seg: RenderMessageSegment):
        if "id" in seg.data:
            return Reply(seg.data["id"], seg.content, seg)

    @build("message")
    def message(self, seg: RenderMessageSegment):
        return Reference(seg.data.get("id"))(*self.generate(seg.children))

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
        if event.reply:
            return Reply(
                str(event.reply.data.get("id")),
                event.reply.content,
                event.reply,
            )
