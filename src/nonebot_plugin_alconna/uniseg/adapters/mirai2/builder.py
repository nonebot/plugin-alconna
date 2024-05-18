from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.mirai2.event import MessageEvent
from nonebot.adapters.mirai2.message import MessageType, MessageSegment

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


class Mirai2MessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.mirai_community

    @build(MessageType.PLAIN)
    def plain(self, seg: MessageSegment):
        return Text(seg.data["text"])

    @build(MessageType.AT)
    def at(self, seg: MessageSegment):
        return At("user", str(seg.data["target"]), seg.data["display"])

    @build(MessageType.AT_ALL)
    def at_all(self, seg: MessageSegment):
        return AtAll()

    @build(MessageType.FACE)
    def face(self, seg: MessageSegment):
        return Emoji(str(seg.data["faceId"]), seg.data["name"])

    @build(MessageType.IMAGE)
    def image(self, seg: MessageSegment):
        return Image(url=seg.data["url"], id=seg.data["imageId"])

    @build(MessageType.VOICE)
    def voice(self, seg: MessageSegment):
        return Voice(url=seg.data["url"], id=seg.data["voiceId"])

    @build(MessageType.FILE)
    def file(self, seg: MessageSegment):
        return File(seg.data["id"], name=seg.data["name"])

    @build(MessageType.QUOTE)
    def quote(self, seg: MessageSegment):
        return Reply(str(seg.data["id"]), seg.data["origin"], origin=seg)

    @build(MessageType.FORWARD)
    def forward(self, seg: MessageSegment):
        nodes = []
        for node in seg.data["nodeList"]:
            if "messageId" in node:
                nodes.append(RefNode(node["messageId"]))
            elif "messageRef" in node:
                nodes.append(RefNode(node["messageRef"]["messageId"], node["messageRef"]["target"]))
            else:
                nodes.append(CustomNode(node["senderId"], node["senderName"], node["time"], node["messageChain"]))
        return Reference(seg.data.get("messageId"))(*nodes)

    @build(MessageType.APP)
    def app(self, seg: MessageSegment):
        return Hyper("json", seg.data["content"])

    @build(MessageType.JSON)
    def json(self, seg: MessageSegment):
        return Hyper("json", seg.data["json"])

    @build(MessageType.XML)
    def xml(self, seg: MessageSegment) -> Hyper:
        return Hyper("xml", seg.data["xml"])

    @build("Video")
    def video(self, seg: MessageSegment):
        return Video(url=seg.data["url"], id=seg.data["videoId"])

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
        if event.quote:
            return Reply(str(event.quote.id), event.quote.origin, event.quote)
