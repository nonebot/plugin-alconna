from nonebot.adapters.ding.message import MessageSegment

from nonebot_plugin_alconna.typings import SegmentPattern

Text = str
AtAll = SegmentPattern("at", MessageSegment, MessageSegment.atAll, lambda x: "isAtAll" in x.data)
AtMobiles = SegmentPattern("at", MessageSegment, MessageSegment.atMobiles, lambda x: "atMobiles" in x.data)
AtDingtalkIds = SegmentPattern(
    "at",
    MessageSegment,
    MessageSegment.atDingtalkIds,
    lambda x: "atDingtalkIds" in x.data,
)
Image = SegmentPattern("image", MessageSegment, MessageSegment.image)
Extension = SegmentPattern("extension", MessageSegment, MessageSegment.extension)
Markdown = SegmentPattern("markdown", MessageSegment, MessageSegment.markdown)
ActionCardSingleBtn = SegmentPattern(
    "actionCard",
    MessageSegment,
    MessageSegment.actionCardSingleBtn,
    lambda x: "singleTitle" in x.data,
)
ActionCardMultiBtns = SegmentPattern(
    "actionCard",
    MessageSegment,
    MessageSegment.actionCardMultiBtns,
    lambda x: "btns" in x.data,
)
FeedCard = SegmentPattern("feedCard", MessageSegment, MessageSegment.feedCard)
Raw = SegmentPattern("raw", MessageSegment, MessageSegment.raw)
