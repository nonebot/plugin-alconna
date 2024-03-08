from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import At, AtAll, Emoji, Hyper, Image, Reply, Video, Voice, Reference


class Onebot11MessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.onebot11

    @build("at")
    def at(self, seg: MessageSegment):
        if seg.data["qq"] != "all":
            return At("user", seg.data["qq"])
        return AtAll()

    @build("face")
    def face(self, seg: MessageSegment):
        return Emoji(seg.data["id"])

    @build("image")
    def image(self, seg: MessageSegment):
        return Image(url=seg.data.get("url"), id=seg.data["file"])

    @build("video")
    def video(self, seg: MessageSegment):
        return Video(url=seg.data.get("url"), id=seg.data["file"])

    @build("record")
    def record(self, seg: MessageSegment):
        return Voice(url=seg.data.get("url"), id=seg.data["file"])

    @build("reply")
    def reply(self, seg: MessageSegment):
        return Reply(seg.data["id"], origin=seg)

    @build("forward")
    def forward(self, seg: MessageSegment):
        return Reference(seg.data["id"])

    @build("json")
    def json(self, seg: MessageSegment):
        return Hyper("json", seg.data["data"])

    @build("xml")
    def xml(self, seg: MessageSegment):
        return Hyper("xml", seg.data["data"])

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
        if _reply := event.reply:
            return Reply(str(_reply.message_id), _reply.message, _reply)
