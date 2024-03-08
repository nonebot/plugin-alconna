from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.qq.message import Ark as ArkSegment
from nonebot.adapters.qq.message import Emoji as EmojiSegment
from nonebot.adapters.qq.models import Message as GuildMessage
from nonebot.adapters.qq.message import Markdown as MarkdownSegment
from nonebot.adapters.qq.message import Reference as ReferenceSegment
from nonebot.adapters.qq.event import QQMessageEvent, GuildMessageEvent
from nonebot.adapters.qq.message import Attachment as AttachmentSegment
from nonebot.adapters.qq.message import MentionUser as MentionUserSegment
from nonebot.adapters.qq.message import MentionChannel as MentionChannelSegment
from nonebot.adapters.qq.message import MentionEveryone as MentionEveryoneSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import At, File, Text, AtAll, Audio, Emoji, Hyper, Image, Reply, Video


class QQMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.qq

    @build("markdown")
    def markdown(self, seg: MarkdownSegment):
        if content := seg.data["markdown"].content:
            return Text(content).mark(0, len(content), "markdown")

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
        return Hyper("json", seg.data["ark"].json())

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
