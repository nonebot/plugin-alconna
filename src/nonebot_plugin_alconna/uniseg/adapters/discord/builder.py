from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.discord import MessageEvent
from nonebot.adapters.discord.message import (
    StickerSegment,
    ReferenceSegment,
    AttachmentSegment,
    CustomEmojiSegment,
    MentionRoleSegment,
    MentionUserSegment,
    MentionChannelSegment,
    MentionEveryoneSegment,
)

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import At, AtAll, Emoji, Image, Reply


class DiscordMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.discord

    @build("mention_user")
    def mention_user(self, seg: MentionUserSegment):
        return At("user", str(seg.data["user_id"]))

    @build("mention_channel")
    def mention_channel(self, seg: MentionChannelSegment):
        return At("channel", str(seg.data["channel_id"]))

    @build("mention_role")
    def mention_role(self, seg: MentionRoleSegment):
        return At("role", str(seg.data["role_id"]))

    @build("mention_everyone")
    def mention_everyone(self, seg: MentionEveryoneSegment):
        return AtAll()

    @build("custom_emoji")
    def custom_emoji(self, seg: CustomEmojiSegment):
        return Emoji(seg.data["id"], seg.data["name"])

    @build("sticker")
    def sticker(self, seg: StickerSegment):
        return Emoji(str(seg.data["id"]))

    @build("attachment")
    def attachment(self, seg: AttachmentSegment):
        return Image(id=seg.data["attachment"].filename)

    @build("reference")
    def reference(self, seg: ReferenceSegment):
        return Reply(seg.data["reference"].message_id, origin=seg.data["reference"])  # type: ignore

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)

        if hasattr(event, "message_reference") and hasattr(event.message_reference, "message_id"):
            return Reply(
                event.message_reference.message_id,  # type: ignore
                origin=event.message_reference,  # type: ignore
            )
