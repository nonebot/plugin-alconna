from nepattern.main import INTEGER
from nonebot.adapters.villa.message import MessageSegment
from nepattern import URL, BasePattern, PatternModel, UnionPattern

from nonebot_plugin_alconna.typings import SegmentPattern

Text = str
MentionUser = SegmentPattern("mention_user", MessageSegment, MessageSegment.mention_user)
MentionRobot = SegmentPattern("mention_robot", MessageSegment, MessageSegment.mention_robot)
MentionAll = SegmentPattern("mention_all", MessageSegment, MessageSegment.mention_all)
RoomLink = SegmentPattern("room_link", MessageSegment, MessageSegment.room_link)
Link = SegmentPattern("link", MessageSegment, MessageSegment.link)
Quote = SegmentPattern("quote", MessageSegment, MessageSegment.quote)
Image = SegmentPattern("image", MessageSegment, MessageSegment.image)
Post = SegmentPattern("post", MessageSegment, MessageSegment.post)
PreviewLink = SegmentPattern("preview_link", MessageSegment, MessageSegment.preview_link)
Badge = SegmentPattern("badge", MessageSegment, MessageSegment.badge)

ImgOrUrl = (
    UnionPattern(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=str,
                converter=lambda _, x: x.data["file_id"],
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

MentionID = (
    UnionPattern(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=int,
                alias="MentionRobot",
                accepts=[MentionRobot],
                converter=lambda _, x: int(x.data["mention_robot"].bot_id),
            ),
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=int,
                alias="MentionUser",
                accepts=[MentionUser],
                converter=lambda _, x: int(x.data["mention_user"].user_id),
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
    @ "mention_id"
)
"""
内置类型，允许传入@用户 或者 @机器人 或者'@xxxx'式样的字符串或者数字, 返回数字
"""
