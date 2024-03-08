from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.feishu.event import MessageEvent
from nonebot.adapters.feishu.message import At as AtSegment
from nonebot.adapters.feishu.message import File as FileSegment
from nonebot.adapters.feishu.message import Post as PostSegment
from nonebot.adapters.feishu.message import Audio as AudioSegment
from nonebot.adapters.feishu.message import Image as ImageSegment
from nonebot.adapters.feishu.message import Media as MediaSegment
from nonebot.adapters.feishu.message import Folder as FolderSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import At, File, AtAll, Audio, Hyper, Image, Reply, Video


class FeishuMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.feishu

    @build("at")
    def at(self, seg: AtSegment):
        if seg.data["user_id"] in ("all", "here"):
            return AtAll(here=seg.data["user_id"] == "here")
        return At("user", str(seg.data["user_id"]))

    @build("image")
    def image(self, seg: ImageSegment):
        return Image(id=seg.data["image_key"])

    @build("media")
    def media(self, seg: MediaSegment):
        return Video(id=seg.data["file_key"], name=seg.data["file_name"] or "video.mp4")

    @build("audio")
    def audio(self, seg: AudioSegment):
        return Audio(url=seg.data["file_key"])

    @build("file")
    def file(self, seg: FileSegment):
        return File(
            id=seg.data["file_key"],
            name=seg.data.get("file_name") or seg.data["file_key"],
        )

    @build("folder")
    def folder(self, seg: FolderSegment):
        return File(
            id=seg.data["file_key"],
            name=seg.data.get("file_name") or seg.data["file_key"],
        )

    @build("post")
    def post(self, seg: PostSegment):
        return Hyper("json", content=dict(seg.data))

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
        if event.reply:
            return Reply(event.reply.message_id, event.reply.body.content, event.reply)
