from arclet.alconna import argv_config, set_default_argv_type
from nonebot.adapters.ding.message import Message, BaseMessage, MessageSegment

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern


class DingMessageArgv(MessageArgv):
    ...


set_default_argv_type(DingMessageArgv)
argv_config(
    DingMessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, BaseMessage),
    to_text=lambda x: x if x.__class__ is str else str(x) if x.is_text() else None,
    converter=lambda x: Message(x),
)

Text = str
AtAll = SegmentPattern(
    "at", MessageSegment, MessageSegment.atAll, lambda x: "isAtAll" in x.data
)
AtMobiles = SegmentPattern(
    "at", MessageSegment, MessageSegment.atMobiles, lambda x: "atMobiles" in x.data
)
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
