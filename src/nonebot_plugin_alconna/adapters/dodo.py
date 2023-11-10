from nepattern.main import URL, INTEGER
from nepattern import BasePattern, PatternModel, UnionPattern
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

from nonebot_plugin_alconna.typings import SegmentPattern

Text = str
At = AtUser = SegmentPattern("at_user", AtUserSegment, MessageSegment.at_user)
ChannelLink = SegmentPattern("channel_link", ChannelLinkSegment, MessageSegment.channel_link)
Reference = SegmentPattern("reference", ReferenceSegment, MessageSegment.reference)
Image = Picture = SegmentPattern("picture", PictureSegment, MessageSegment.picture)
Video = SegmentPattern("video", VideoSegment, MessageSegment.video)
Card = SegmentPattern("card", CardSegment, MessageSegment.card)
AtRole = SegmentPattern("at_role", AtRoleSegment, AtRoleSegment)
AtAll = SegmentPattern("at_all", AtAllSegment, AtAllSegment)
Share = SegmentPattern("share", ShareSegment, ShareSegment)
File = SegmentPattern("file", FileSegment, FileSegment)

ImgOrUrl = (
    UnionPattern(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=str,
                converter=lambda _, x: x.data["picture"].url,
                alias="img",
                accepts=[Image],
            ),
            URL,
        ]
    )
    @ "img_url"
)
"""
内置类型, 允许传入图片元素(Image)或者链接(URL)，返回链接
"""

AtID = (
    UnionPattern(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=int,
                alias="AtUser",
                accepts=[AtUser],
                converter=lambda _, x: int(x.data["dodo_id"]),
            ),
            BasePattern(
                r"@(\d+)",
                model=PatternModel.REGEX_CONVERT,
                origin=int,
                alias="@xxx",
                accepts=[str],
                converter=lambda _, x: int(x[1]),
            ),
            INTEGER,
        ]
    )
    @ "at_id"
)
"""
内置类型，允许传入提醒元素(AtUser)或者'@xxxx'式样的字符串或者数字, 返回数字
"""
