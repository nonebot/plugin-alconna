import re

from nonebot.adapters.kaiheila.message import Message
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

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern

CHN = re.compile(r"\(chn\)(?P<id>.+?)\(chn\)")
EMJ = re.compile(r"\(emj\)(?P<name>.+?)\(emj\)\[(?P<id>[^\[]+?)\]")
EMJ1 = re.compile(r":(?P<id>.+?):")
NO_CHN = re.compile(r"\[\(chn\)(?P<id>.+?)\(chn\)\]\(.+\)")
NO_EMJ = re.compile(r"\[\(emj\)(?P<name>.+?)\(emj\)\[(?P<id>[^\[]+?)\]\]\(.+\)")
NO_EMJ1 = re.compile(r"\[:(?P<id>.+?):\]\(.+\)")


def builder(self: MessageArgv, data: Message):
    for index, unit in enumerate(data):
        if not self.is_text(unit):
            self.raw_data.append(unit)
            self.ndata += 1
            continue
        if unit.type == "text":
            text = unit.data["text"]
            if not text.strip():
                if not index or index == len(data) - 1:
                    continue
                if not self.is_text(data[index - 1]) or not self.is_text(data[index + 1]):
                    continue
            if self.raw_data and self.raw_data[-1].__class__ is str:
                self.raw_data[-1] = f"{self.raw_data[-1]}{text}"
            else:
                self.raw_data.append(text)
                self.ndata += 1
            continue
        content = unit.data["content"]
        mats = {}
        spans = {}
        for mat in CHN.finditer(content):
            mats[mat.start()] = MessageSegment("mention_channel", {"channel_id": mat.group("id")})
            spans[mat.start()] = mat.end()
        for mat in EMJ.finditer(content):
            mats[mat.start()] = MessageSegment("emoji", {"id": mat.group("id"), "name": mat.group("name")})
            spans[mat.start()] = mat.end()
        for mat in EMJ1.finditer(content):
            mats[mat.start()] = MessageSegment("emoji", {"id": mat.group("id")})
            spans[mat.start()] = mat.end()
        for mat in NO_CHN.finditer(content):
            if mat.start() + 1 in spans:
                del spans[mat.start() + 1]
                del mats[mat.start() + 1]
        for mat in NO_EMJ.finditer(content):
            if mat.start() + 1 in spans:
                del spans[mat.start() + 1]
                del mats[mat.start() + 1]
        for mat in NO_EMJ1.finditer(content):
            if mat.start() + 1 in spans:
                del spans[mat.start() + 1]
                del mats[mat.start() + 1]
        if not mats:
            self.raw_data.append(content)
            self.ndata += 1
            continue
        text = ""
        in_mat = False
        current = 0
        for _index, char in enumerate(content):
            if _index in spans:
                in_mat = True
                current = _index
                if text:
                    self.raw_data.append(text)
                    self.ndata += 1
                    text = ""
                self.raw_data.append(mats[_index])
                self.ndata += 1
                continue
            if _index >= spans[current]:
                in_mat = False
            if not in_mat:
                text += char
        if text:
            self.raw_data.append(text)
            self.ndata += 1


MessageArgv.custom_build(Message, builder=builder)  # type: ignore


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
