from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.kritor.event import MessageEvent
from nonebot.adapters.kritor.message import At as AtSegment
from nonebot.adapters.kritor.message import Xml as XmlSegment
from nonebot.adapters.kritor.message import Face as FaceSegment
from nonebot.adapters.kritor.message import File as FileSegment
from nonebot.adapters.kritor.message import Json as JsonSegment
from nonebot.adapters.kritor.message import Image as ImageSegment
from nonebot.adapters.kritor.message import Reply as ReplySegment
from nonebot.adapters.kritor.message import Video as VideoSegment
from nonebot.adapters.kritor.message import Voice as VoiceSegment
from nonebot.adapters.kritor.message import Forward as ForwardSegment
from nonebot.adapters.kritor.message import Keyboard as KeyboardSegment
from nonebot.adapters.kritor.message import Markdown as MarkdownSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import (
    At,
    File,
    Text,
    AtAll,
    Emoji,
    Hyper,
    Image,
    Other,
    Reply,
    Video,
    Voice,
    Reference,
)


class KritorMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.kritor

    @build("at")
    def at(self, seg: AtSegment):
        if seg.data["uid"] != "all":
            return At("user", seg.data["uid"])
        return AtAll()

    @build("face")
    def face(self, seg: FaceSegment):
        return Emoji(str(seg.data["id"]))

    @build("image")
    def image(self, seg: ImageSegment):
        return Image(url=seg.data.get("file_url"), id=seg.data.get("file_md5"))

    @build("video")
    def video(self, seg: VideoSegment):
        return Video(url=seg.data.get("file_url"), id=seg.data.get("file_md5"))

    @build("voice")
    def record(self, seg: VoiceSegment):
        return Voice(url=seg.data.get("file_url"), id=seg.data.get("file_md5"))

    @build("file")
    def file(self, seg: FileSegment):
        return File(id=seg.data.get("file_id"), name=seg.data.get("name", "file.bin"), url=seg.data.get("url"))

    @build("reply")
    def reply(self, seg: ReplySegment):
        return Reply(seg.data["message_id"], origin=seg)

    @build("forward")
    def forward(self, seg: ForwardSegment):
        return Reference(seg.data["res_id"])

    @build("json")
    def json(self, seg: JsonSegment):
        return Hyper("json", seg.data["json"])

    @build("xml")
    def xml(self, seg: XmlSegment):
        return Hyper("xml", seg.data["xml"])

    @build("markdown")
    def markdown(self, seg: MarkdownSegment):
        return Text(seg.data["markdown"], styles={(0, len(seg.data["markdown"])): ["markdown"]})

    @build("keyboard")
    def keyboard(self, seg: KeyboardSegment):
        return Other(seg)

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
        if _reply := event.reply:
            return Reply(
                str(_reply.data["message_id"]), event.replied_message.message if event.replied_message else None, _reply
            )
