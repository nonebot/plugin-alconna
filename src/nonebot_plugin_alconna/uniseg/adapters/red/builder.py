from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.red.event import MessageEvent
from nonebot.adapters.red.message import MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import At, File, AtAll, Emoji, Hyper, Image, Reply, Video, Voice, Reference


class RedMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.red

    @build("at")
    def at(self, seg: MessageSegment):
        return At("user", str(seg.data["user_id"]), seg.data.get("user_name"))

    @build("at_all")
    def at_all(self, seg: MessageSegment):
        return AtAll()

    @build("face")
    def face(self, seg: MessageSegment):
        return Emoji(str(seg.data["face_id"]))

    @build("image")
    def image(self, seg: MessageSegment):
        return Image(
            id=seg.data["uuid"],
            path=seg.data["path"],
            name=seg.data["md5"],
        )

    @build("video")
    def video(self, seg: MessageSegment):
        return Video(
            id=seg.data["videoMd5"],
            path=seg.data["filePath"],
            name=seg.data["fileName"],
        )

    @build("voice")
    def voice(self, seg: MessageSegment):
        return Voice(
            id=seg.data["md5"],
            path=seg.data["path"],
            name=seg.data["name"],
        )

    @build("file")
    def file(self, seg: MessageSegment):
        return File(
            id=seg.data["md5"],
            name=seg.data["name"],
        )

    @build("reply")
    def reply(self, seg: MessageSegment):
        return Reply(f'{seg.data["msg_id"]}#{seg.data["msg_seq"]}', origin=seg.data["_origin"])

    @build("forward")
    def forward(self, seg: MessageSegment):
        return Reference(seg.data["id"])

    @build("ark")
    def ark(self, seg: MessageSegment):
        return Hyper("json", seg.data["data"])

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)

        if event.reply:
            return Reply(
                f"{event.reply.sourceMsgIdInRecords}#{event.reply.replayMsgSeq}",
                event.reply.sourceMsgTextElems,
                origin=event.reply,
            )
