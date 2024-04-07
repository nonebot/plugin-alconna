from pathlib import Path
from base64 import b64decode
from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.satori.event import MessageEvent
from nonebot.adapters.satori.message import At as AtSegment
from nonebot.adapters.satori.message import File as FileSegment
from nonebot.adapters.satori.message import Link as LinkSegment
from nonebot.adapters.satori.message import Text as TextSegment
from nonebot.adapters.satori.message import Audio as AudioSegment
from nonebot.adapters.satori.message import Image as ImageSegment
from nonebot.adapters.satori.message import Sharp as SharpSegment
from nonebot.adapters.satori.message import Video as VideoSegment
from nonebot.adapters.satori.message import Button as ButtonSegment
from nonebot.adapters.satori.message import Custom as CustomSegment
from nonebot.adapters.satori.message import RenderMessage as RenderMessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import (
    At,
    File,
    Text,
    AtAll,
    Audio,
    Emoji,
    Image,
    Other,
    Reply,
    Video,
    Reference,
)

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


class SatoriMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.satori

    @build("text")
    def text(self, seg: TextSegment):
        styles = {scale: [STYLE_TYPE_MAP.get(s, s) for s in _styles] for scale, _styles in seg.data["styles"].items()}
        return Text(seg.data["text"], styles)

    @build("at")
    def at(self, seg: AtSegment):
        if "type" in seg.data and seg.data["type"] in ("all", "here"):
            return AtAll(here=seg.data["type"] == "here")
        if "id" in seg.data:
            return At("user", seg.data["id"], seg.data.get("name"))
        if "role" in seg.data:
            return At("role", seg.data["role"], seg.data.get("name"))

    @build("sharp")
    def sharp(self, seg: SharpSegment):
        return At("channel", seg.data["id"], seg.data.get("name"))

    @build("link")
    def link(self, seg: LinkSegment):
        display = seg.data.get("display")
        return Text(seg.data["text"]).mark(0, len(seg.data["text"]), f"link:{display}" if display else "link")

    @build("img", "image")
    def image(self, seg: ImageSegment):
        src = seg.data["src"]
        if src.startswith("http"):
            return Image(url=src)
        if src.startswith("file://"):
            return Image(path=Path(src[7:]))
        if src.startswith("data:"):
            mime, b64 = src[5:].split(";", 1)
            return Image(raw=b64decode(b64[7:]), mimetype=mime)
        return Image(seg.data["src"])

    @build("audio")
    def audio(self, seg: AudioSegment):
        src = seg.data["src"]
        if src.startswith("http"):
            return Audio(url=src)
        if src.startswith("file://"):
            return Audio(path=Path(src[7:]))
        if src.startswith("data:"):
            mime, b64 = src[5:].split(";", 1)
            return Audio(raw=b64decode(b64[7:]), mimetype=mime)
        return Audio(seg.data["src"])

    @build("video")
    def video(self, seg: VideoSegment):
        src = seg.data["src"]
        if src.startswith("http"):
            return Video(url=src)
        if src.startswith("file://"):
            return Video(path=Path(src[7:]))
        if src.startswith("data:"):
            mime, b64 = src[5:].split(";", 1)
            return Video(raw=b64decode(b64[7:]), mimetype=mime)
        return Video(seg.data["src"])

    @build("file")
    def file(self, seg: FileSegment):
        src = seg.data["src"]
        if src.startswith("http"):
            return File(url=src)
        if src.startswith("file://"):
            return File(path=Path(src[7:]))
        if src.startswith("data:"):
            mime, b64 = src[5:].split(";", 1)
            return File(raw=b64decode(b64[7:]), mimetype=mime)
        return File(seg.data["src"])

    @build("quote")
    def quote(self, seg: RenderMessageSegment):
        if "id" in seg.data:
            return Reply(seg.data["id"], seg.data.get("content"), seg)

    @build("message")
    def message(self, seg: RenderMessageSegment):
        return Reference(seg.data.get("id"), seg.data.get("content"))

    @build("button")
    def button(self, seg: ButtonSegment):
        return Other(seg)

    @build("chronocat:face")
    def emoji(self, seg: CustomSegment):
        return Emoji(seg.data["id"], seg.data.get("name"))  # type: ignore

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
        if event.reply:
            return Reply(
                str(event.reply.data.get("id")),
                event.reply.data.get("content"),
                event.reply,
            )
