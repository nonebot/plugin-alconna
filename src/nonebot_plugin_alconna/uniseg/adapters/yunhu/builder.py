from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.yunhu.event import MessageEvent
from nonebot.adapters.yunhu.message import At as AtSegment
from nonebot.adapters.yunhu.message import Buttons as ButtonsSegment
from nonebot.adapters.yunhu.message import Face as FaceSegment
from nonebot.adapters.yunhu.message import File as FileSegment
from nonebot.adapters.yunhu.message import Html as HtmlSegment
from nonebot.adapters.yunhu.message import Image as ImageSegment
from nonebot.adapters.yunhu.message import Markdown as MarkdownSegment
from nonebot.adapters.yunhu.message import Message
from nonebot.adapters.yunhu.message import Text as TextSegment
from nonebot.adapters.yunhu.message import Video as VideoSegment
from nonebot.adapters.yunhu.models import Reply as ReplySegement

from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.segment import At, Button, Emoji, File, Image, Keyboard, Reply, Text, Video


class YunHuMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.yunhu

    @build("text")
    def text(self, seg: TextSegment):
        return Text(seg.data["text"])

    @build("markdown")
    def markdown(self, seg: MarkdownSegment):
        content = seg.data["text"]
        return Text(content).mark(0, len(content), "markdown")

    @build("html")
    def html(self, seg: HtmlSegment):
        content = seg.data["text"]
        return Text(content).mark(0, len(content), "html")

    @build("at")
    def at(self, seg: AtSegment):
        return At("user", seg.data["user_id"], seg.data["name"])

    @build("face")
    def face(self, seg: FaceSegment):
        return Emoji(seg.data["code"], seg.data["emoji"])

    @build("image")
    def image(self, seg: ImageSegment):

        if seg.data["url"]:
            return Image(id=seg.data["imageKey"], url=seg.data["url"])
        if seg.data["raw"]:
            return Image(id=seg.data["imageKey"], raw=seg.data["raw"])
        return Image(id=seg.data["imageKey"])

    @build("video")
    def video(self, seg: VideoSegment):
        if seg.data["url"]:
            return Video(id=seg.data["videoKey"], url=seg.data["url"])
        if seg.data["raw"]:
            return Video(id=seg.data["videoKey"], raw=seg.data["raw"])
        return Video(id=seg.data["videoKey"])

    @build("file")
    def file(self, seg: FileSegment):
        if seg.data["url"]:
            return File(id=seg.data["fileKey"], url=seg.data["url"])
        if seg.data["raw"]:
            return File(id=seg.data["fileKey"], raw=seg.data["raw"])
        return File(id=seg.data["fileKey"])

    @build("keyboard")
    def keyboard(self, seg: ButtonsSegment):
        kbs = []
        btns = seg.data["buttons"]
        for kb in btns:
            buttons = []
            for button in kb:
                if button["actionType"] == 1:
                    flag = "link"
                elif button["actionType"] == 2:
                    flag = "input"
                elif button["actionType"] == 3:
                    flag = "action"
                buttons.append(
                    Button(
                        flag=flag,
                        label=button["text"],
                        url=button["url"] if button["actionType"] == 1 else None,
                        text=button["value"] if button["actionType"] == 2 else None,
                    )
                )
            kbs.append(Keyboard(buttons=buttons))
        return kbs

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
        if rpl := event.reply:
            if TYPE_CHECKING:
                assert isinstance(rpl, ReplySegement)
            return Reply(
                rpl.msgId,
                Message.deserialize(rpl.content, rpl.content.at, rpl.contentType, rpl.commandName),
                rpl,
            )
        return None
