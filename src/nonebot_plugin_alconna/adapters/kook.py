from nonebot.adapters.kaiheila.message import Card as _Card
from nonebot.adapters.kaiheila.message import File as _File
from nonebot.adapters.kaiheila.message import MessageSegment
from nonebot.adapters.kaiheila.message import Audio as _Audio
from nonebot.adapters.kaiheila.message import Image as _Image
from nonebot.adapters.kaiheila.message import Quote as _Quote
from nonebot.adapters.kaiheila.message import Video as _Video
from nonebot.adapters.kaiheila.message import Mention as _Mention
from nonebot.adapters.kaiheila.message import KMarkdown as _KMarkdown
from nonebot.adapters.kaiheila.message import MentionAll as _MentionAll
from nonebot.adapters.kaiheila.message import MentionHere as _MentionHere
from nonebot.adapters.kaiheila.message import MentionRole as _MentionRole

from nonebot_plugin_alconna.typings import SegmentPattern


def mention_channel(channel_id: str):
    return MessageSegment.KMarkdown(f"(chn){channel_id}(chn)", f"(chn){channel_id}(chn)")


def emoji(id: str, name: str = ""):
    if name:
        return MessageSegment.KMarkdown(f"(emj){name}(emj)[{id}]")
    else:
        return MessageSegment.KMarkdown(f":{id}:")


Text = str

Mention = At = SegmentPattern("mention", _Mention, MessageSegment.mention)
MentionRole = AtRole = SegmentPattern("mention_role", _MentionRole, MessageSegment.mention_role)
MentionChannel = AtChannel = SegmentPattern("mention_channel", MessageSegment, mention_channel)
MentionAll = AtAll = SegmentPattern("mention_all", _MentionAll, MessageSegment.mention_all)
MentionHere = AtHere = SegmentPattern("mention_here", _MentionHere, MessageSegment.mention_here)
Emoji = SegmentPattern("emoji", MessageSegment, emoji)

Image = SegmentPattern("image", _Image, MessageSegment.image)
Video = SegmentPattern("video", _Video, MessageSegment.video)
File = SegmentPattern("file", _File, MessageSegment.file)
Audio = SegmentPattern("audio", _Audio, MessageSegment.audio)
Card = SegmentPattern("card", _Card, MessageSegment.Card)
Quote = SegmentPattern("quote", _Quote, MessageSegment.quote)


class KMPattern(SegmentPattern):
    def match(self, input_) -> MessageSegment:
        if isinstance(input_, str):
            return MessageSegment.KMarkdown(input_, input_)
        return super().match(input_)


KMarkdown = KMPattern("kmarkdown", _KMarkdown, MessageSegment.KMarkdown)
