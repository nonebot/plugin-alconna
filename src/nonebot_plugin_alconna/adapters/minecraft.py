from nonebot.adapters.minecraft.message import MessageSegment

from nonebot_plugin_alconna.typings import SegmentPattern

Text = str
Image = SegmentPattern("image", MessageSegment, MessageSegment.image)
Video = SegmentPattern("video", MessageSegment, MessageSegment.video)
