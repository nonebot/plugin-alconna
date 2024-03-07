from typing import List

from nonebot.adapters.telegram.message import File
from nepattern import MatchMode, BasePattern, UnionPattern
from nonebot.adapters.telegram.message import Reply as _Reply
from nonebot.adapters.telegram.message import Entity, Message, UnCombinFile, MessageSegment

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern, StyleTextPattern


def is_text(x: MessageSegment):
    return x.type in {
        "text",
        "bot_command",
        "bold",
        "italic",
        "underline",
        "strikethrough",
        "spoiler",
        "code",
    }


styles = {
    "record": {},
    "index": 0,
    "msg": "",
}


def builder(self: MessageArgv, data: Message):
    styles["msg"] = str(data)
    _index = 0
    for index, unit in enumerate(data):
        if not self.is_text(unit):
            self.raw_data.append(unit)
            self.ndata += 1
            continue
        if not unit.data["text"].strip():
            if not index or index == len(data) - 1:
                continue
            if not self.is_text(data[index - 1]) or not self.is_text(data[index + 1]):
                continue
        text = unit.data["text"]
        if unit.type == "text":
            self.raw_data.append(text)
            self.ndata += 1
            continue
        if self.raw_data and self.raw_data[-1].__class__ is str:
            self.raw_data[-1] = f"{self.raw_data[-1]}{text}"
        else:
            self.raw_data.append(text)
            self.ndata += 1
        start = styles["msg"].find(text, _index)
        _index = start + len(text)
        styles["record"][(start, _index)] = unit.type


def clean_style():
    styles["record"].clear()
    styles["index"] = 0


MessageArgv.custom_build(Message, is_text=is_text, builder=builder, cleanup=clean_style)  # type: ignore


def locator(x: str, t: List[str]):
    start = styles["msg"].find(x, styles["index"])
    if start == -1:
        return
    styles["index"] = start + len(x)
    if (maybe := styles["record"].get((start, styles["index"]))) and maybe == t[0]:
        return Entity(maybe, {"text": x})
    if any(
        scale[0] <= start <= scale[1] and scale[0] <= styles["index"] <= scale[1] and styles["record"][scale] == t[0]
        for scale in styles["record"]
    ):
        return Entity(t[0], {"text": x})
    return


Text = str
Location = SegmentPattern("location", MessageSegment, MessageSegment.location)
Venue = SegmentPattern("venue", MessageSegment, MessageSegment.venue)
Poll = SegmentPattern("poll", MessageSegment, MessageSegment.poll)
Dice = SegmentPattern("dice", MessageSegment, MessageSegment.dice)
ChatAction = SegmentPattern("chat_action", MessageSegment, MessageSegment.chat_action)

Mention = SegmentPattern("mention", Entity, Entity.mention)
Hashtag = SegmentPattern("hashtag", Entity, Entity.hashtag)
Cashtag = SegmentPattern("cashtag", Entity, Entity.cashtag)
Url = SegmentPattern("url", Entity, Entity.url)
Email = SegmentPattern("email", Entity, Entity.email)
PhoneNumber = SegmentPattern("phone_number", Entity, Entity.phone_number)

BotCommand = StyleTextPattern("bot_command", Entity, Entity.bot_command, locator)
Bold = StyleTextPattern("bold", Entity, Entity.bold, locator)
Italic = StyleTextPattern("italic", Entity, Entity.italic, locator)
Underline = StyleTextPattern("underline", Entity, Entity.underline, locator)
Strikethrough = StyleTextPattern("strikethrough", Entity, Entity.strikethrough, locator)
Spoiler = StyleTextPattern("spoiler", Entity, Entity.spoiler, locator)
Code = StyleTextPattern("code", Entity, Entity.code, locator)

Pre = SegmentPattern("pre", Entity, Entity.pre)
TextLink = SegmentPattern("text_link", Entity, Entity.text_link)
TextMention = SegmentPattern("text_mention", Entity, Entity.text_mention)
CustomEmoji = SegmentPattern("custom_emoji", Entity, Entity.custom_emoji)

Image = Photo = SegmentPattern("photo", File, File.photo)
Voice = SegmentPattern("voice", File, File.voice)
Animation = SegmentPattern("animation", File, File.animation)
Audio = SegmentPattern("audio", File, File.audio)
Document = SegmentPattern("document", File, File.document)
Video = SegmentPattern("video", File, File.video)

Reply = SegmentPattern("reply", _Reply, _Reply.reply)

Sticker = SegmentPattern("sticker", UnCombinFile, UnCombinFile.sticker)
VideoNote = SegmentPattern("video_note", UnCombinFile, UnCombinFile.video_note)

Mentions = UnionPattern([Mention, TextMention, TextLink])
"""联合接收 Mention, TextMention, TextLink, 不能用于发送"""

Videos = UnionPattern([Video, Animation])
"""联合接收 Video, Animation, 不能用于发送"""

ImgOrUrl = UnionPattern(
    [
        BasePattern(
            mode=MatchMode.TYPE_CONVERT,
            origin=str,
            converter=lambda _, x: x.data["file_id"],
            alias="img",
            addition_accepts=Image,
        ),
        BasePattern(
            mode=MatchMode.TYPE_CONVERT,
            origin=str,
            converter=lambda _, x: x.data["text"],
            alias="url",
            addition_accepts=Url,
        ),
    ]
)
"""
内置类型, 允许传入图片元素(Image)或者链接(URL)，返回链接
"""
