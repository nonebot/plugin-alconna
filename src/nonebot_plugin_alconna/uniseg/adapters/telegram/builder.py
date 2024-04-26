from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.telegram.message import Entity
from nonebot.adapters.telegram.event import MessageEvent
from nonebot.adapters.telegram.message import File as FileSegment
from nonebot.adapters.telegram.message import Reply as ReplySegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import At, File, Text, Audio, Emoji, Image, Reply, Video, Voice


class TelegramMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.telegram

    @build("mention")
    def mention(self, seg: Entity):
        return At("user", seg.data["text"])

    @build("text_mention")
    def text_mention(self, seg: Entity):
        return At("user", str(seg.data["user"].id), seg.data["text"])

    @build("custom_emoji")
    def custom_emoji(self, seg: Entity):
        return Emoji(seg.data["custom_emoji_id"], seg.data["text"])

    @build("photo")
    def photo(self, seg: FileSegment):
        return Image(id=seg.data["file"])

    @build("video", "animation")
    def video(self, seg: FileSegment):
        return Video(id=seg.data["file_id"])

    @build("voice")
    def voice(self, seg: FileSegment):
        return Voice(id=seg.data["file_id"])

    @build("audio")
    def audio(self, seg: FileSegment):
        return Audio(id=seg.data["file_id"])

    @build("document")
    def document(self, seg: FileSegment):
        return File(seg.data["file_id"], name=seg.data["file_name"])

    @build("reply")
    def reply(self, seg: ReplySegment):
        return Reply(str(seg.data["message_id"]), origin=seg)

    @build("hashtag")
    def hashtag(self, seg: Entity):
        return Text(seg.data["text"])

    @build("cashtag")
    def cashtag(self, seg: Entity):
        return Text(seg.data["text"])

    @build("bot_command")
    def bot_command(self, seg: Entity):
        return Text(seg.data["text"]).mark(0, len(seg.data["text"]), "bot_command")

    @build("url")
    def url(self, seg: Entity):
        return Text(seg.data["text"]).mark(0, len(seg.data["text"]), "link")

    @build("email")
    def email(self, seg: Entity):
        return Text(seg.data["text"])

    @build("phone_number")
    def phone_number(self, seg: Entity):
        return Text(seg.data["text"])

    @build("bold")
    def bold(self, seg: Entity):
        return Text(seg.data["text"]).mark(0, len(seg.data["text"]), "bold")

    @build("italic")
    def italic(self, seg: Entity):
        return Text(seg.data["text"]).mark(0, len(seg.data["text"]), "italic")

    @build("underline")
    def underline(self, seg: Entity):
        return Text(seg.data["text"]).mark(0, len(seg.data["text"]), "underline")

    @build("strikethrough")
    def strikethrough(self, seg: Entity):
        return Text(seg.data["text"]).mark(0, len(seg.data["text"]), "strikethrough")

    @build("code")
    def code(self, seg: Entity):
        return Text(seg.data["text"]).mark(0, len(seg.data["text"]), "code")

    @build("pre")
    def pre(self, seg: Entity):
        return Text(seg.data["text"]).mark(0, len(seg.data["text"]), f"pre:{seg.data['language']}")

    @build("text_link")
    def text_link(self, seg: Entity):
        text = Text(seg.data["url"]).mark(0, len(seg.data["url"]), "link")
        text._children = [Text(seg.data["text"])]
        return text

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)
        if event.reply_to_message:
            return Reply(
                f"{event.reply_to_message.message_id}",
                event.reply_to_message.original_message,
                event.reply_to_message,
            )
