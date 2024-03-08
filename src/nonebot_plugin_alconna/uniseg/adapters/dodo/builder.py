from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.dodo import MessageEvent
from nonebot.adapters.dodo.message import (
    FileSegment,
    AtAllSegment,
    VideoSegment,
    AtRoleSegment,
    AtUserSegment,
    PictureSegment,
    ReferenceSegment,
    ChannelLinkSegment,
)

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import At, File, AtAll, Image, Reply


class DodoMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.dodo

    @build("at_user")
    def at_user(self, seg: AtUserSegment):
        return At("user", seg.data["dodo_id"])

    @build("at_role")
    def at_role(self, seg: AtRoleSegment):
        return At("role", seg.data["role_id"])

    @build("channel_link")
    def channel_link(self, seg: ChannelLinkSegment):
        return At("channel", seg.data["channel_id"])

    @build("at_all")
    def mention_everyone(self, seg: AtAllSegment):
        return AtAll()

    @build("picture")
    def picture(self, seg: PictureSegment):
        return Image(url=seg.data["picture"].url)

    @build("video")
    def video(self, seg: VideoSegment):
        return Image(url=seg.data["video"].url)

    @build("file")
    def file(self, seg: FileSegment):
        return File(url=seg.data["file"].url)

    @build("reference")
    def reference(self, seg: ReferenceSegment):
        return Reply(seg.data["message_id"], origin=seg)

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, MessageEvent)

        if reply := event.reply:
            return Reply(reply.message_id, origin=reply)
