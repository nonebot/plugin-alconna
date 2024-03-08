from nonebot.adapters.dodo.message import (
    CardSegment,
    FileSegment,
    AtAllSegment,
    ShareSegment,
    VideoSegment,
    AtRoleSegment,
    AtUserSegment,
    MessageSegment,
    PictureSegment,
    ReferenceSegment,
    ChannelLinkSegment,
)

from nonebot_plugin_alconna.uniseg import At as UniAt
from nonebot_plugin_alconna.uniseg import Other, Reply
from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot_plugin_alconna.uniseg import File as UniFile
from nonebot_plugin_alconna.uniseg import AtAll as UniAtAll
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.uniseg import Video as UniVideo

At = AtUser = SegmentPattern("at_user", AtUserSegment, UniAt, MessageSegment.at_user)
ChannelLink = SegmentPattern("channel_link", ChannelLinkSegment, UniAt, MessageSegment.channel_link)
Reference = SegmentPattern("reference", ReferenceSegment, Reply, MessageSegment.reference)
Image = Picture = SegmentPattern("picture", PictureSegment, UniImage, MessageSegment.picture)
Video = SegmentPattern("video", VideoSegment, UniVideo, MessageSegment.video)
Card = SegmentPattern("card", CardSegment, Other, MessageSegment.card)
AtRole = SegmentPattern("at_role", AtRoleSegment, UniAt, AtRoleSegment)
AtAll = SegmentPattern("at_all", AtAllSegment, UniAtAll, AtAllSegment)
Share = SegmentPattern("share", ShareSegment, Other, ShareSegment)
File = SegmentPattern("file", FileSegment, UniFile, FileSegment)
