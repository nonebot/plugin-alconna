from mimetypes import guess_type
from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.discord import MessageEvent
from nonebot.adapters.discord.api.model import TextInput
from nonebot.adapters.discord.api.model import Button as ButtonModel
from nonebot.adapters.discord.message import (
    StickerSegment,
    ComponentSegment,
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
from nonebot_plugin_alconna.uniseg.segment import At, File, AtAll, Audio, Image, Other, Reply, Video, Button, Keyboard


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
        url = f"https://cdn.discordapp.com/emojis/{seg.data['id']}.{'gif' if seg.data['animated'] else 'png'}"
        return Image(url=url, id=url, name=f"{seg.data['name']}.{'gif' if seg.data['animated'] else 'png'}")

    @build("sticker")
    def sticker(self, seg: StickerSegment):
        url = f"https://cdn.discordapp.com/stickers/{seg.data['id']}.gif"
        return Image(url=url, id=url, name=f"{seg.data['id']}.gif")

    @build("attachment")
    def attachment(self, seg: AttachmentSegment):
        mtype = guess_type(seg.data["attachment"].filename)[0]
        if mtype and mtype.startswith("image"):
            return Image(id=seg.data["attachment"].filename, name=seg.data["attachment"].filename)
        if mtype and mtype.startswith("video"):
            return Video(id=seg.data["attachment"].filename, name=seg.data["attachment"].filename)
        if mtype and mtype.startswith("audio"):
            return Audio(id=seg.data["attachment"].filename, name=seg.data["attachment"].filename)
        return File(
            id=seg.data["attachment"].filename,
            name=seg.data["attachment"].filename,
        )

    @build("reference")
    def reference(self, seg: ReferenceSegment):
        return Reply(seg.data["reference"].message_id, origin=seg.data["reference"])  # type: ignore

    @build("component")
    def component(self, seg: ComponentSegment):
        comp = seg.data["component"]
        if isinstance(comp, TextInput):
            return Button(
                flag="input",
                id=comp.custom_id,
                label=comp.label,
                clicked_label=comp.placeholder or None,  # type: ignore
            )
        buttons = []
        for _comp in comp.components:
            if isinstance(_comp, ButtonModel):
                buttons.append(
                    Button(
                        flag="link" if isinstance(_comp.url, str) else "action",
                        id=_comp.custom_id or None,  # type: ignore
                        label=_comp.label or "button",  # type: ignore
                        url=_comp.url if isinstance(_comp.url, str) else None,
                        style=_comp.style.name.lower(),
                    )
                )
            elif isinstance(_comp, TextInput):
                buttons.append(
                    Button(
                        flag="input",
                        id=_comp.custom_id,
                        label=_comp.label,
                        clicked_label=_comp.placeholder or None,  # type: ignore
                    )
                )
        if buttons:
            return Keyboard(buttons=buttons)
        return Other(seg)

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)

        if hasattr(event, "message_reference") and hasattr(event.message_reference, "message_id"):
            return Reply(
                event.message_reference.message_id,  # type: ignore
                origin=event.message_reference,  # type: ignore
            )
        return None
