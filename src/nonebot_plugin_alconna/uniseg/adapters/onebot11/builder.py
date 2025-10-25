from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment

from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.segment import At, AtAll, Emoji, File, Hyper, Image, Reference, Reply, Video, Voice


class Onebot11MessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.onebot11

    @build("at")
    def at(self, seg: MessageSegment):
        if seg.data["qq"] == "all":
            return AtAll()
        if int(seg.data["qq"]) == 0:
            return AtAll()
        return At("user", str(seg.data["qq"]))

    @build("face")
    def face(self, seg: MessageSegment):
        return Emoji(str(seg.data["id"]))

    @build("image")
    def image(self, seg: MessageSegment):
        is_sticker = seg.data.get("subType") == 1 or seg.data.get("sub_type") == 1
        return Image(url=seg.data.get("url") or seg.data.get("file"), id=seg.data["file"], sticker=is_sticker)

    @build("video")
    def video(self, seg: MessageSegment):
        return Video(url=seg.data.get("url") or seg.data.get("file"), id=seg.data["file"])

    @build("record")
    def record(self, seg: MessageSegment):
        return Voice(url=seg.data.get("url") or seg.data.get("file"), id=seg.data["file"])

    @build("reply")
    def reply(self, seg: MessageSegment):
        return Reply(str(seg.data["id"]), origin=seg)

    @build("forward")
    def forward(self, seg: MessageSegment):
        return Reference(seg.data["id"])

    @build("json")
    def json(self, seg: MessageSegment):
        return Hyper("json", seg.data["data"])

    @build("xml")
    def xml(self, seg: MessageSegment):
        return Hyper("xml", seg.data["data"])

    @build("file")
    def file(self, seg: MessageSegment):
        url = seg.data.get("url") or seg.data.get("file")
        name = seg.data.get("file_name") or seg.data.get("file")
        return File(id=seg.data["file_id"], name=name or "file.bin", url=url)

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
        if _reply := event.reply:
            return Reply(str(_reply.message_id), _reply.message, _reply)
        return None
