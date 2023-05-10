from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot.adapters.kaiheila.message import MessageSegment
from nonebot_plugin_alconna.argv import MessageArgv
from arclet.alconna import set_default_argv_type

set_default_argv_type(MessageArgv)

Text = str
At = SegmentPattern("at", MessageSegment, MessageSegment.at)
Image = SegmentPattern("image", MessageSegment, MessageSegment.image)
Video = SegmentPattern("video", MessageSegment, MessageSegment.video)
File = SegmentPattern("file", MessageSegment, MessageSegment.file)
Audio = SegmentPattern("audio", MessageSegment, MessageSegment.audio)
KMarkdown = SegmentPattern("kmarkdown", MessageSegment, MessageSegment.kmarkdown)
Card = SegmentPattern("card", MessageSegment, MessageSegment.card)
Quote = SegmentPattern("quote", MessageSegment, MessageSegment.quote)
