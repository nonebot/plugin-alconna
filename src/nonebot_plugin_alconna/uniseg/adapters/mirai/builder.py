from datetime import datetime
from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.mirai.message import IdNode
from nonebot.adapters.mirai.event import MessageEvent
from nonebot.adapters.mirai.message import At as AtSegment
from nonebot.adapters.mirai.message import App as AppSegment
from nonebot.adapters.mirai.message import Xml as XmlSegment
from nonebot.adapters.mirai.message import Face as FaceSegment
from nonebot.adapters.mirai.message import File as FileSegment
from nonebot.adapters.mirai.message import Json as JsonSegment
from nonebot.adapters.mirai.message import Text as TextSegment
from nonebot.adapters.mirai.message import AtAll as AtAllSegment
from nonebot.adapters.mirai.message import Image as ImageSegment
from nonebot.adapters.mirai.message import Video as VideoSegment
from nonebot.adapters.mirai.message import Voice as VoiceSegment
from nonebot.adapters.mirai.message import Forward as ForwardSegment
from nonebot.adapters.mirai.message import RefNode as RefNodeSegment
from nonebot.adapters.mirai.message import MarketFace as MarketFaceSegment

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
    Reply,
    Video,
    Voice,
    RefNode,
    Reference,
    CustomNode,
)


class MiraiMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.mirai_official

    @build("text")
    def plain(self, seg: TextSegment):
        return Text(seg.data["text"])

    @build("at")
    def at(self, seg: AtSegment):
        return At("user", str(seg.data["target"]), seg.data["display"])

    @build("at_all")
    def at_all(self, seg: AtAllSegment):
        return AtAll()

    @build("face")
    def face(self, seg: FaceSegment):
        return Emoji(str(seg.data["id"]), seg.data["name"])

    @build("market_face")
    def market_face(self, seg: MarketFaceSegment):
        return Emoji(str(seg.data["id"]), seg.data["name"])

    @build("image")
    def image(self, seg: ImageSegment):
        return Image(url=seg.data["url"], id=seg.data["id"])

    @build("voice")
    def voice(self, seg: VoiceSegment):
        return Voice(url=seg.data["url"], id=seg.data["id"], duration=seg.data["length"])

    @build("video")
    def video(self, seg: VideoSegment):
        return Video(url=seg.data["url"], id=seg.data["id"])

    @build("file")
    def file(self, seg: FileSegment):
        return File(seg.data["id"], name=seg.data["name"])

    @build("forward")
    def forward(self, seg: ForwardSegment):
        nodes = []
        for node in seg.data["nodes"]:
            if isinstance(node, IdNode):
                nodes.append(RefNode(str(node.id)))
            elif isinstance(node, RefNodeSegment):
                nodes.append(RefNode(str(node.ref["id"]), str(node.ref["target"])))
            else:
                nodes.append(CustomNode(str(node.uid), node.name, datetime.fromtimestamp(node.time), node.message))
        return Reference()(*nodes)

    @build("app")
    def app(self, seg: AppSegment):
        return Hyper("json", seg.data["content"])

    @build("json")
    def json(self, seg: JsonSegment):
        return Hyper("json", seg.data["json"])

    @build("xml")
    def xml(self, seg: XmlSegment) -> Hyper:
        return Hyper("xml", seg.data["xml"])

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
        if event.reply:
            return Reply(str(event.reply.id), event.reply.origin, event.reply)
