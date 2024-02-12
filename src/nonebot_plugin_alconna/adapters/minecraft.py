from nonebot.adapters.minecraft.message import MessageSegment

from nonebot_plugin_alconna.typings import SegmentPattern

Text = str
Title = SegmentPattern("title", MessageSegment, MessageSegment.title)
ActionBar = SegmentPattern("actionbar", MessageSegment, MessageSegment.actionbar)
