from nonebot.adapters.onebot.v12.message import MessageSegment

from nonebot_plugin_alconna.uniseg import At
from nonebot_plugin_alconna.uniseg import AtAll
from nonebot_plugin_alconna.uniseg import Other
from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot_plugin_alconna.uniseg import File as UniFile
from nonebot_plugin_alconna.uniseg import Audio as UniAudio
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.uniseg import Reply as UniReply
from nonebot_plugin_alconna.uniseg import Video as UniVideo

Mention = SegmentPattern("mention", MessageSegment, At, MessageSegment.mention)
MentionAll = SegmentPattern("mention_all", MessageSegment, AtAll, MessageSegment.mention_all)
Image = SegmentPattern("image", MessageSegment, UniImage, MessageSegment.image)
Audio = SegmentPattern("audio", MessageSegment, UniAudio, MessageSegment.audio)
Voice = SegmentPattern("voice", MessageSegment, UniVideo, MessageSegment.voice)
File = SegmentPattern("file", MessageSegment, UniFile, MessageSegment.file)
Video = SegmentPattern("video", MessageSegment, UniVideo, MessageSegment.video)
Location = SegmentPattern("location", MessageSegment, Other, MessageSegment.location)
Reply = SegmentPattern("reply", MessageSegment, UniReply, MessageSegment.reply)
