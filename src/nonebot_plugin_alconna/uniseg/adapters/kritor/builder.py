from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.kritor.event import MessageEvent
from nonebot.adapters.kritor.message import At as AtSegment
from nonebot.adapters.kritor.message import Xml as XmlSegment
from nonebot.adapters.kritor.message import Face as FaceSegment
from nonebot.adapters.kritor.message import File as FileSegment
from nonebot.adapters.kritor.message import Json as JsonSegment
from nonebot.adapters.kritor.message import Image as ImageSegment
from nonebot.adapters.kritor.message import Reply as ReplySegment
from nonebot.adapters.kritor.message import Video as VideoSegment
from nonebot.adapters.kritor.message import Voice as VoiceSegment
from nonebot.adapters.kritor.message import Forward as ForwardSegment
from nonebot.adapters.kritor.message import Keyboard as KeyboardSegment
from nonebot.adapters.kritor.message import Markdown as MarkdownSegment

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
    Button,
    Keyboard,
    Reference,
)


class KritorMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.kritor

    @build("at")
    def at(self, seg: AtSegment):
        if seg.data["uid"] != "all":
            return At("user", seg.data["uid"])
        return AtAll()

    @build("face")
    def face(self, seg: FaceSegment):
        return Emoji(str(seg.data["id"]))

    @build("image")
    def image(self, seg: ImageSegment):
        return Image(url=seg.data.get("file_url"), id=seg.data.get("file_md5"))

    @build("video")
    def video(self, seg: VideoSegment):
        return Video(url=seg.data.get("file_url"), id=seg.data.get("file_md5"))

    @build("voice")
    def record(self, seg: VoiceSegment):
        return Voice(url=seg.data.get("file_url"), id=seg.data.get("file_md5"))

    @build("file")
    def file(self, seg: FileSegment):
        return File(id=seg.data.get("id"), name=seg.data.get("name", "file.bin"), url=seg.data.get("url"))

    @build("reply")
    def reply(self, seg: ReplySegment):
        return Reply(seg.data["message_id"], origin=seg)

    @build("forward")
    def forward(self, seg: ForwardSegment):
        return Reference(seg.data["res_id"])

    @build("json")
    def json(self, seg: JsonSegment):
        return Hyper("json", seg.data["json"])

    @build("xml")
    def xml(self, seg: XmlSegment):
        return Hyper("xml", seg.data["xml"])

    @build("markdown")
    def markdown(self, seg: MarkdownSegment):
        return Text(seg.data["markdown"], styles={(0, len(seg.data["markdown"])): ["markdown"]})

    @build("keyboard")
    def keyboard(self, seg: KeyboardSegment):
        buttons = []
        for row in seg.data["rows"]:
            for button in row["buttons"]:
                if button.action.type == 0:
                    flag = "link"
                elif button.action.type == 1:
                    flag = "action"
                elif button.action.enter:
                    flag = "enter"
                else:
                    flag = "input"
                perm = "all"
                if button.action.permission:
                    permission = button.action.permission
                    if permission.type == 0:
                        assert permission.user_ids
                        perm = [At("user", i) for i in permission.user_ids]
                    elif permission.type == 1:
                        perm = "admin"
                    elif permission.type == 2:
                        perm = "all"
                    else:
                        assert permission.role_ids
                        perm = [At("role", i) for i in permission.role_ids]
                buttons.append(
                    Button(
                        flag=flag,  # type: ignore
                        id=button.id,
                        label=button.render_data.label,
                        clicked_label=button.render_data.visited_label,
                        url=button.action.data if button.action.type == 0 else None,
                        text=button.action.data if button.action.type == 2 else None,
                        style="grey" if button.render_data.style == 0 else "blue",
                        permission=perm,
                    )
                )
        return Keyboard(id=str(seg.data["bot_appid"]), buttons=buttons, row=len(buttons) // len(seg.data["rows"]))

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
        if _reply := event.reply:
            return Reply(
                str(_reply.data["message_id"]), event.replied_message.message if event.replied_message else None, _reply
            )
        return None
