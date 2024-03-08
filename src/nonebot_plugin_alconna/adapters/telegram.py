from nepattern import UnionPattern
from nonebot.adapters.telegram.message import File
from nonebot.adapters.telegram.message import Reply as _Reply
from nonebot.adapters.telegram.message import Entity, UnCombinFile, MessageSegment

from nonebot_plugin_alconna.uniseg import At
from nonebot_plugin_alconna.uniseg import Emoji
from nonebot_plugin_alconna.uniseg import Other
from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot_plugin_alconna.uniseg import File as UniFile
from nonebot_plugin_alconna.uniseg import Audio as UniAudio
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.uniseg import Reply as UniReply
from nonebot_plugin_alconna.uniseg import Video as UniVideo
from nonebot_plugin_alconna.uniseg import Voice as UniVoice

Location = SegmentPattern("location", MessageSegment, Other, MessageSegment.location)
Venue = SegmentPattern("venue", MessageSegment, Other, MessageSegment.venue)
Poll = SegmentPattern("poll", MessageSegment, Other, MessageSegment.poll)
Dice = SegmentPattern("dice", MessageSegment, Other, MessageSegment.dice)
ChatAction = SegmentPattern("chat_action", MessageSegment, Other, MessageSegment.chat_action)

Mention = SegmentPattern("mention", Entity, At, Entity.mention)

TextMention = SegmentPattern("text_mention", Entity, At, Entity.text_mention)
CustomEmoji = SegmentPattern("custom_emoji", Entity, Emoji, Entity.custom_emoji)

Image = Photo = SegmentPattern("photo", File, UniImage, File.photo)
Voice = SegmentPattern("voice", File, UniVoice, File.voice)
Animation = SegmentPattern("animation", File, UniVideo, File.animation)
Audio = SegmentPattern("audio", File, UniAudio, File.audio)
Document = SegmentPattern("document", File, UniFile, File.document)
Video = SegmentPattern("video", File, UniVideo, File.video)

Reply = SegmentPattern("reply", _Reply, UniReply, _Reply.reply)

Sticker = SegmentPattern("sticker", UnCombinFile, Other, UnCombinFile.sticker)
VideoNote = SegmentPattern("video_note", UnCombinFile, Other, UnCombinFile.video_note)

Mentions = UnionPattern([Mention, TextMention])
"""联合接收 Mention, TextMention, TextLink, 不能用于发送"""

Videos = UnionPattern([Video, Animation])
"""联合接收 Video, Animation, 不能用于发送"""
