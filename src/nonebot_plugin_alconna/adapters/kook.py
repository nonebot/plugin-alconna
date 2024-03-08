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

from nonebot_plugin_alconna.uniseg import Hyper
from nonebot_plugin_alconna.uniseg import Reply
from nonebot_plugin_alconna.uniseg import At as UniAt
from nonebot_plugin_alconna.uniseg import File as UniFile
from nonebot_plugin_alconna.uniseg import Text as UniText
from nonebot_plugin_alconna.uniseg import AtAll as UniAtAll
from nonebot_plugin_alconna.uniseg import Audio as UniAudio
from nonebot_plugin_alconna.uniseg import Emoji as UniEmoji
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.uniseg import Video as UniVideo
from nonebot_plugin_alconna.typings import SegmentPattern, TextSegmentPattern


def mention_channel(channel_id: str):
    return MessageSegment.KMarkdown(f"(chn){channel_id}(chn)", f"(chn){channel_id}(chn)")


def emoji(id: str, name: str = ""):
    if name:
        return MessageSegment.KMarkdown(f"(emj){name}(emj)[{id}]")
    else:
        return MessageSegment.KMarkdown(f":{id}:")


Mention = At = SegmentPattern("mention", _Mention, UniAt, MessageSegment.mention)
MentionRole = AtRole = SegmentPattern("mention_role", _MentionRole, UniAt, MessageSegment.mention_role)
MentionChannel = AtChannel = SegmentPattern("mention_channel", MessageSegment, UniAt, mention_channel)
MentionAll = AtAll = SegmentPattern("mention_all", _MentionAll, UniAtAll, MessageSegment.mention_all)
MentionHere = AtHere = SegmentPattern("mention_here", _MentionHere, UniAtAll, MessageSegment.mention_here)
Emoji = SegmentPattern("emoji", MessageSegment, UniEmoji, emoji)

Image = SegmentPattern("image", _Image, UniImage, MessageSegment.image)
Video = SegmentPattern("video", _Video, UniVideo, MessageSegment.video)
File = SegmentPattern("file", _File, UniFile, MessageSegment.file)
Audio = SegmentPattern("audio", _Audio, UniAudio, MessageSegment.audio)
Card = SegmentPattern("card", _Card, Hyper, MessageSegment.Card, handle=lambda x: MessageSegment.Card(x.raw))
Quote = SegmentPattern("quote", _Quote, Reply, MessageSegment.quote)


def kmarkdown(self, text: UniText):
    if text.extract_most_style() == "markdown":
        return MessageSegment.KMarkdown(text.text, text.text)


KMarkdown = TextSegmentPattern("kmarkdown", _KMarkdown, MessageSegment.KMarkdown, kmarkdown)
