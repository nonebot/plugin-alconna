from nonebot.adapters.kaiheila.message import Message, MessageSegment

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern

MessageArgv.custom_build(
    Message,
    is_text=lambda x: x.type == "text",
)


def at(user_id: str):
    return MessageSegment.KMarkdown(f"(met){user_id}(met)", user_id)


Text = str
At = SegmentPattern("at", MessageSegment, at)
Image = SegmentPattern("image", MessageSegment, MessageSegment.image)
Video = SegmentPattern("video", MessageSegment, MessageSegment.video)
File = SegmentPattern("file", MessageSegment, MessageSegment.file)
Audio = SegmentPattern("audio", MessageSegment, MessageSegment.audio)
KMarkdown = SegmentPattern("kmarkdown", MessageSegment, MessageSegment.KMarkdown)
Card = SegmentPattern("card", MessageSegment, MessageSegment.Card)
Quote = SegmentPattern("quote", MessageSegment, MessageSegment.quote)
