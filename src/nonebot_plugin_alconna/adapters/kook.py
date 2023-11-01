from nonebot.adapters.kaiheila.message import Message, MessageSegment

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern

MessageArgv.custom_build(
    Message,
    is_text=lambda x: x.type == "text",
)


def at(user_id: str):
    return MessageSegment.KMarkdown(f"(met){user_id}(met)", user_id)


def atall(here: bool = False):
    return MessageSegment.KMarkdown(f"(met){'here' if here else 'all'}(met)")


def is_at(segment: MessageSegment):
    content = segment.data["content"]
    if not content.startswith("(met)"):
        return False
    if (end := content.find("(met)", 5)) == -1:
        return False
    return content[5:end] not in ("here", "all")


def is_atall(segment: MessageSegment):
    content = segment.data["content"]
    if not content.startswith("(met)"):
        return False
    if (end := content.find("(met)", 5)) == -1:
        return False
    return content[5:end] in ("here", "all")


Text = str
At = SegmentPattern("at", MessageSegment, at, is_at)
AtAll = SegmentPattern("at", MessageSegment, atall, is_atall)
Image = SegmentPattern("image", MessageSegment, MessageSegment.image)
Video = SegmentPattern("video", MessageSegment, MessageSegment.video)
File = SegmentPattern("file", MessageSegment, MessageSegment.file)
Audio = SegmentPattern("audio", MessageSegment, MessageSegment.audio)
KMarkdown = SegmentPattern("kmarkdown", MessageSegment, MessageSegment.KMarkdown)
Card = SegmentPattern("card", MessageSegment, MessageSegment.Card)
Quote = SegmentPattern("quote", MessageSegment, MessageSegment.quote)
