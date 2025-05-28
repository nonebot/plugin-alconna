from base64 import b64decode
from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.milky.message import XML
from nonebot.adapters.milky.event import MessageEvent
from nonebot.adapters.milky.message import Face as FaceSegment
from nonebot.adapters.milky.message import Image as ImageSegment
from nonebot.adapters.milky.message import Reply as ReplySegment
from nonebot.adapters.milky.message import Video as VideoSegment
from nonebot.adapters.milky.message import Record as RecordSegment
from nonebot.adapters.milky.message import Forward as ForwardSegment
from nonebot.adapters.milky.message import Mention as MentionSegment
from nonebot.adapters.milky.message import LightAPP as LightAppSegment
from nonebot.adapters.milky.message import MentionAll as MentionAllSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import (
    At,
    AtAll,
    Emoji,
    Hyper,
    Image,
    Reply,
    Video,
    Voice,
    Reference,
    CustomNode,
)


class MilkyMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.milky

    @build("mention")
    def mention(self, seg: MentionSegment):
        if seg.data["user_id"] == 0:
            return AtAll()
        return At("user", str(seg.data["user_id"]))

    @build("mention_all")
    def mention_all(self, seg: MentionAllSegment):
        return AtAll()

    @build("face")
    def face(self, seg: FaceSegment):
        return Emoji(str(seg.data["face_id"]))

    @build("image")
    def image(self, seg: ImageSegment):
        if "resource_id" in seg.data:
            return Image(id=seg.data["resource_id"], url=seg.data.get("temp_url"))
        uri = seg.data["uri"]
        if uri.startswith("http"):
            return Image(url=uri)
        if uri.startswith("file://"):
            return Image(path=uri[7:])
        if uri.startswith("base64://"):
            b64 = uri[9:]
            return Image(raw=b64decode(b64))

    @build("video")
    def video(self, seg: VideoSegment):
        if "resource_id" in seg.data:
            return Video(id=seg.data["resource_id"], url=seg.data.get("temp_url"))
        uri = seg.data["uri"]
        thumbnail = None
        if thumb_url := seg.data.get("thumb_url"):
            thumbnail = Image(url=thumb_url)
        if uri.startswith("http"):
            return Video(url=uri, thumbnail=thumbnail)
        if uri.startswith("file://"):
            return Video(path=uri[7:], thumbnail=thumbnail)
        if uri.startswith("base64://"):
            b64 = uri[9:]
            return Video(raw=b64decode(b64), thumbnail=thumbnail)

    @build("record")
    def record(self, seg: RecordSegment):
        if "resource_id" in seg.data:
            return Voice(id=seg.data["resource_id"], url=seg.data.get("temp_url"), duration=seg.data["duration"])
        uri = seg.data["uri"]
        if uri.startswith("http"):
            return Voice(url=uri)
        if uri.startswith("file://"):
            return Voice(path=uri[7:])
        if uri.startswith("base64://"):
            b64 = uri[9:]
            return Voice(raw=b64decode(b64))

    @build("reply")
    def reply(self, seg: ReplySegment):
        if "client_seq" in seg.data:
            msg_id = f"{seg.data['message_seq']}#{seg.data['client_seq']}"
        else:
            msg_id = str(seg.data["message_seq"])
        return Reply(msg_id, origin=seg)

    @build("forward")
    def forward(self, seg: ForwardSegment):
        if "forward_id" in seg.data:
            return Reference(seg.data["forward_id"])
        return Reference(
            nodes=[
                CustomNode(uid=str(msg.user_id), name=msg.name, content=self.generate(msg.segments))
                for msg in seg.data["messages"]
            ]
        )

    @build("light_app")
    def light_app(self, seg: LightAppSegment):
        return Hyper("json", seg.data["json_payload"])

    @build("xml")
    def xml(self, seg: XML):
        return Hyper("xml", seg.data["xml_payload"])

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
        if _reply := event.reply:
            if _reply.client_seq:
                msg_id = f"{_reply.message_seq}#{_reply.client_seq}"
            else:
                msg_id = str(_reply.message_seq)
            return Reply(msg_id, _reply.message, _reply)
        return None
