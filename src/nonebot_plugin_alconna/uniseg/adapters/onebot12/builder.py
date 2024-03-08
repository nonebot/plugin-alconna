from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v12.event import MessageEvent
from nonebot.adapters.onebot.v12.message import MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import At, File, AtAll, Audio, Image, Reply, Video, Voice


class Onebot12MessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.onebot12

    @build("mention")
    def mention(self, seg: MessageSegment):
        return At("user", seg.data["user_id"])

    @build("mention_all")
    def mention_all(self, seg: MessageSegment):
        return AtAll()

    @build("image")
    def image(self, seg: MessageSegment):
        return Image(id=seg.data["file_id"])

    @build("video")
    def video(self, seg: MessageSegment):
        return Video(id=seg.data["file_id"])

    @build("audio")
    def audio(self, seg: MessageSegment):
        return Audio(id=seg.data["file_id"])

    @build("voice")
    def voice(self, seg: MessageSegment):
        return Voice(id=seg.data["file_id"])

    @build("file")
    def file(self, seg: MessageSegment):
        return File(id=seg.data["file_id"])

    @build("reply")
    def reply(self, seg: MessageSegment):
        return Reply(seg.data["message_id"], origin=seg)

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
        if _reply := event.reply:
            return Reply(str(_reply.message_id), None, _reply)
