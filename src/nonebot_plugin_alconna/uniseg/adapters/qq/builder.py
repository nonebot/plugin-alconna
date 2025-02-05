from typing import TYPE_CHECKING

from nonebot.compat import model_dump
from nonebot.adapters import Bot, Event
from nonebot.adapters.qq.message import Ark as ArkSegment
from nonebot.adapters.qq.message import Emoji as EmojiSegment
from nonebot.adapters.qq.models import Message as GuildMessage
from nonebot.adapters.qq.message import Keyboard as KeyboardSegment
from nonebot.adapters.qq.message import Markdown as MarkdownSegment
from nonebot.adapters.qq.message import Reference as ReferenceSegment
from nonebot.adapters.qq.event import QQMessageEvent, GuildMessageEvent
from nonebot.adapters.qq.message import Attachment as AttachmentSegment
from nonebot.adapters.qq.message import MentionUser as MentionUserSegment
from nonebot.adapters.qq.message import MentionChannel as MentionChannelSegment
from nonebot.adapters.qq.message import MentionEveryone as MentionEveryoneSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import (
    At,
    File,
    Text,
    AtAll,
    Audio,
    Emoji,
    Hyper,
    Image,
    Reply,
    Video,
    Button,
    Keyboard,
)


class QQMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.qq

    @build("markdown")
    def markdown(self, seg: MarkdownSegment):
        if content := seg.data["markdown"].content:
            return Text(content).mark(0, len(content), "markdown")
        return None

    @build("mention_user")
    def mention(self, seg: MentionUserSegment):
        return At("user", seg.data["user_id"])

    @build("mention_channel")
    def mention_channel(self, seg: MentionChannelSegment):
        return At("channel", str(seg.data["channel_id"]))

    @build("mention_everyone")
    def mention_all(self, seg: MentionEveryoneSegment):
        return AtAll()

    @build("emoji")
    def emoji(self, seg: EmojiSegment):
        return Emoji(seg.data["id"])

    @build("attachment")
    def attachment(self, seg: AttachmentSegment):
        return Image(url=seg.data["url"])

    @build("image")
    def image(self, seg: AttachmentSegment):
        if "filename" in seg.data:
            return Image(
                url=seg.data["url"],
                id=seg.data["filename"],
                mimetype=seg.data["content_type"],
                name=seg.data["filename"],
            )
        return Image(url=seg.data["url"])

    @build("video")
    def video(self, seg: AttachmentSegment):
        if "filename" in seg.data:
            return Video(
                url=seg.data["url"],
                id=seg.data["filename"],
                mimetype=seg.data["content_type"],
                name=seg.data["filename"],
            )
        return Video(url=seg.data["url"])

    @build("audio")
    def audio(self, seg: AttachmentSegment):
        if "filename" in seg.data:
            return Audio(
                url=seg.data["url"],
                id=seg.data["filename"],
                mimetype=seg.data["content_type"],
                name=seg.data["filename"],
            )
        return Audio(url=seg.data["url"])

    @build("file")
    def file(self, seg: AttachmentSegment):
        if "filename" in seg.data:
            return File(
                url=seg.data["url"],
                id=seg.data["filename"],
                mimetype=seg.data["content_type"],
                name=seg.data["filename"],
            )
        return File(url=seg.data["url"])

    @build("reference")
    def reference(self, seg: ReferenceSegment):
        return Reply(seg.data["reference"].message_id, origin=seg.data["reference"])

    @build("ark")
    def ark(self, seg: ArkSegment):
        return Hyper("json", content=model_dump(seg.data["ark"]))

    @build("keyboard")
    def keyboard(self, seg: KeyboardSegment):
        buttons = []
        model = seg.data["keyboard"]
        if not model.content:
            return Keyboard(id=model.id)
        assert model.content.rows
        for row in model.content.rows:
            assert row.buttons
            for button in row.buttons:
                assert button.action
                assert button.render_data
                assert button.render_data.label
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
                        assert permission.specify_user_ids
                        perm = [At("user", i) for i in permission.specify_user_ids]
                    elif permission.type == 1:
                        perm = "admin"
                    elif permission.type == 2:
                        perm = "all"
                    else:
                        assert permission.specify_role_ids
                        perm = [At("role", i) for i in permission.specify_role_ids]
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
        return Keyboard(buttons=buttons, row=len(buttons) // len(model.content.rows))

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, (GuildMessageEvent, QQMessageEvent))
        if rpl := getattr(event, "reply", None):
            if TYPE_CHECKING:
                assert isinstance(rpl, GuildMessage)
            return Reply(
                str(rpl.id),
                rpl.content,
                rpl,
            )
        return None
