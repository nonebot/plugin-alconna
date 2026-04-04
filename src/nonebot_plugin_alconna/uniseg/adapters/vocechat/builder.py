from nonebot.adapters import Bot, Event
from nonebot.adapters.vocechat.event import MessageEvent
from nonebot.adapters.vocechat.message import MessageSegment

from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.segment import At, Audio, File, Image, Reply, Text, Video


class VocechatMessageBuilder(MessageBuilder[MessageSegment]):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.vocechat

    @build("text")
    def text(self, seg: MessageSegment):
        return Text(seg.data["text"])

    @build("markdown")
    def markdown(self, seg: MessageSegment):
        content = seg.data["text"]
        return Text(content).mark(0, len(content), "markdown")

    @build("mention")
    def mention(self, seg: MessageSegment):
        return At("user", str(seg.data["user_id"]))

    @build("image")
    def image(self, seg: MessageSegment):
        file = seg.data["file"]
        properties = seg.data.get("properties") or {}
        return Image(
            id=file.file_id,
            name=file.filename or Image.__default_name__,
            width=properties.get("width"),
            height=properties.get("height"),
        )

    @build("audio")
    def audio(self, seg: MessageSegment):
        file = seg.data["file"]
        return Audio(id=file.file_id, name=file.filename or Audio.__default_name__)

    @build("video")
    def video(self, seg: MessageSegment):
        file = seg.data["file"]
        return Video(id=file.file_id, name=file.filename or Video.__default_name__)

    @build("file")
    def file(self, seg: MessageSegment):
        file = seg.data["file"]
        return File(id=file.file_id, name=file.filename or File.__default_name__)

    async def extract_reply(self, event: Event, bot: Bot):
        if isinstance(event, MessageEvent) and event.reply:
            return Reply(str(event.reply.mid), event.reply.message, event.reply)
        return None
