import re

from nonebot.adapters.kaiheila.message import Message, MessageSegment

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern

MET = re.compile(r"\(met\)(?P<id>.+?)\(met\)")
CHN = re.compile(r"\(chn\)(?P<id>.+?)\(chn\)")
ROLE = re.compile(r"\(role\)(?P<id>.+?)\(role\)")
EMJ = re.compile(r"\(emj\)(?P<name>.+?)\(emj\)\[(?P<id>[^\[]+?)\]")
EMJ1 = re.compile(r":(?P<id>.+?):")
NO_MET = re.compile(r"\[\(met\)(?P<id>.+?)\(met\)\]\(.+\)")
NO_CHN = re.compile(r"\[\(chn\)(?P<id>.+?)\(chn\)\]\(.+\)")
NO_ROLE = re.compile(r"\[\(role\)(?P<id>.+?)\(role\)\]\(.+\)")
NO_EMJ = re.compile(r"\[\(emj\)(?P<name>.+?)\(emj\)\[(?P<id>[^\[]+?)\]\]\(.+\)")
NO_EMJ1 = re.compile(r"\[:(?P<id>.+?):\]\(.+\)")


def builder(self: MessageArgv, data: Message):
    for index, unit in enumerate(data):
        if not self.is_text(unit):
            self.raw_data.append(unit)
            self.ndata += 1
            continue
        if unit.type == "text":
            text = unit.data["content"]
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
        for mat in MET.finditer(content):
            mats[mat.start()] = MessageSegment(
                "at", {"user_id": mat.group("id"), "user_name": mat.group("id")}
            )
            spans[mat.start()] = mat.end()
        for mat in CHN.finditer(content):
            mats[mat.start()] = MessageSegment("at_channel", {"channel_id": mat.group("id")})
            spans[mat.start()] = mat.end()
        for mat in ROLE.finditer(content):
            mats[mat.start()] = MessageSegment("at_role", {"role_id": mat.group("id")})
            spans[mat.start()] = mat.end()
        for mat in EMJ.finditer(content):
            mats[mat.start()] = MessageSegment("emoji", {"id": mat.group("id"), "name": mat.group("name")})
            spans[mat.start()] = mat.end()
        for mat in EMJ1.finditer(content):
            mats[mat.start()] = MessageSegment("emoji", {"id": mat.group("id")})
            spans[mat.start()] = mat.end()
        for mat in NO_MET.finditer(content):
            if mat.start() + 1 in spans:
                del spans[mat.start() + 1]
                del mats[mat.start() + 1]
        for mat in NO_CHN.finditer(content):
            if mat.start() + 1 in spans:
                del spans[mat.start() + 1]
                del mats[mat.start() + 1]
        for mat in NO_ROLE.finditer(content):
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


def at(user_id: str):
    return MessageSegment.KMarkdown(f"(met){user_id}(met)", f"(met){user_id}(met)")


def at_role(role_id: str):
    return MessageSegment.KMarkdown(f"(role){role_id}(role)", f"(role){role_id}(role)")


def at_channel(channel_id: str):
    return MessageSegment.KMarkdown(f"(chn){channel_id}(chn)", f"(chn){channel_id}(chn)")


def atall(here: bool = False):
    return MessageSegment.KMarkdown(f"(met){'here' if here else 'all'}(met)")


def emoji(id: str, name: str = ""):
    if name:
        return MessageSegment.KMarkdown(f"(emj){name}(emj)[{id}]")
    else:
        return MessageSegment.KMarkdown(f":{id}:")


def is_at(segment: MessageSegment):
    return segment.type == "at" and segment.data["user_id"] not in ("all", "here")


def is_at_all(segment: MessageSegment):
    return segment.type == "at" and segment.data["user_id"] in ("all", "here")


Text = str

At = SegmentPattern("at", MessageSegment, at, is_at)
AtRole = SegmentPattern("at_role", MessageSegment, at_role)
AtChannel = SegmentPattern("at_channel", MessageSegment, at_channel)
AtAll = SegmentPattern("at", MessageSegment, atall, is_at_all)
Emoji = SegmentPattern("emoji", MessageSegment, emoji)

Image = SegmentPattern("image", MessageSegment, MessageSegment.image)
Video = SegmentPattern("video", MessageSegment, MessageSegment.video)
File = SegmentPattern("file", MessageSegment, MessageSegment.file)
Audio = SegmentPattern("audio", MessageSegment, MessageSegment.audio)
Card = SegmentPattern("card", MessageSegment, MessageSegment.Card)
Quote = SegmentPattern("quote", MessageSegment, MessageSegment.quote)


class KMPattern(SegmentPattern):
    def match(self, input_) -> MessageSegment:
        if isinstance(input_, str):
            return MessageSegment.KMarkdown(input_, input_)
        return super().match(input_)


KMarkdown = KMPattern("kmarkdown", MessageSegment, MessageSegment.KMarkdown)
