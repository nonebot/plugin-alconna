from nonebot.adapters.ding.message import MessageSegment

from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot_plugin_alconna.uniseg import AtAll, Image, Other

AtAll = SegmentPattern("at", MessageSegment, AtAll, MessageSegment.atAll)
AtMobiles = SegmentPattern(
    "at", MessageSegment, Other, MessageSegment.atMobiles, lambda x: "atMobiles" in x.origin.data
)
AtDingtalkIds = SegmentPattern(
    "at",
    MessageSegment,
    Other,
    MessageSegment.atDingtalkIds,
    lambda x: "atDingtalkIds" in x.origin.data,
)
Image = SegmentPattern(
    "image", MessageSegment, Image, MessageSegment.image, handle=lambda x: MessageSegment.image(x.url)  # type: ignore
)
Extension = SegmentPattern(
    "extension",
    MessageSegment,
    Other,
    MessageSegment.extension,
)
Markdown = SegmentPattern(
    "markdown",
    MessageSegment,
    Other,
    MessageSegment.markdown,
)

ActionCardSingleBtn = SegmentPattern(
    "actionCard",
    MessageSegment,
    Other,
    MessageSegment.actionCardSingleBtn,
    lambda x: "singleTitle" in x.origin.data,
)

ActionCardMultiBtns = SegmentPattern(
    "actionCard",
    MessageSegment,
    Other,
    MessageSegment.actionCardMultiBtns,
    lambda x: "btns" in x.origin.data,
)

FeedCard = SegmentPattern(
    "feedCard",
    MessageSegment,
    Other,
    MessageSegment.feedCard,
)

Raw = SegmentPattern(
    "raw",
    MessageSegment,
    Other,
    MessageSegment.raw,
)
