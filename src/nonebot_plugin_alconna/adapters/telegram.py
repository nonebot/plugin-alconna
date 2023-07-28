from typing import Iterable, Any

from typing_extensions import Self

from tarina import lang
from nepattern import UnionPattern
from arclet.alconna import NullMessage, argv_config, set_default_argv_type
from nonebot.adapters.telegram.message import (
    File,
    Entity,
    Message,
    BaseMessage,
    UnCombinFile,
    MessageSegment,
)

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern, TextSegmentPattern


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


class TelegramMessageArgv(MessageArgv):
    def reset(self):
        super().reset()
        styles["record"].clear()
        styles["index"] = 0

    def addon(self, data: Iterable[Any]) -> Self:
        """添加命令元素

        Args:
            data (Iterable[str | Any]): 命令元素

        Returns:
            Self: 自身
        """
        self.raw_data = self.bak_data.copy()
        for i, d in enumerate(data):
            if not d:
                continue
            if not is_text(d):
                self.raw_data.append(d)
                self.ndata += 1
                continue
            text = d.data["text"]
            if i > 0 and isinstance(self.raw_data[-1], str):
                self.raw_data[-1] += f"{self.separators[0]}{text}"
            else:
                self.raw_data.append(text)
                self.ndata += 1
        self.current_index = 0
        self.bak_data = self.raw_data.copy()
        if self.message_cache:
            self.token = self.generate_token(self.raw_data)
        return self

    def build(self, data: BaseMessage) -> Self:
        """命令分析功能, 传入字符串或消息链

        Args:
            data (TDC): 命令

        Returns:
            Self: 自身
        """
        self.reset()
        if not isinstance(data, BaseMessage):
            raise TypeError(data)
        self.origin = data
        styles["msg"] = str(data)
        _index = 0
        raw_data = self.raw_data
        for index, unit in enumerate(data):
            if not is_text(unit):
                raw_data.append(unit)
                self.ndata += 1
                continue
            if not unit.data["text"].strip():
                if not index or index == len(data) - 1:
                    continue
                if not is_text(data[index - 1]) or not is_text(data[index + 1]):
                    continue
            text = unit.data["text"]
            if unit.type == "text":
                raw_data.append(text)
                self.ndata += 1
                continue
            if raw_data and raw_data[-1].__class__ is str:
                raw_data[-1] = f"{raw_data[-1]}{text}"
            else:
                raw_data.append(text)
                self.ndata += 1
            start = styles["msg"].find(text, _index)
            _index = start + len(text)
            styles["record"][(start, _index)] = unit.type
        if self.ndata < 1:
            raise NullMessage(lang.require("argv", "null_message").format(target=data))
        self.bak_data = raw_data.copy()
        if self.message_cache:
            self.token = self.generate_token(raw_data)
        return self


def locator(x: str, t: str):
    start = styles["msg"].find(x, styles["index"])
    if start == -1:
        return False
    styles["index"] = start + len(x)
    if (maybe := styles["record"].get((start, styles["index"]))) and maybe == t:
        return True
    return any(
        scale[0] <= start <= scale[1]
        and scale[0] <= styles["index"] <= scale[1]
        and styles["record"][scale] == t
        for scale in styles["record"]
    )


set_default_argv_type(TelegramMessageArgv)
argv_config(TelegramMessageArgv, converter=lambda x: Message(x))

Text = str
Location = SegmentPattern("location", MessageSegment, MessageSegment.location)
Venue = SegmentPattern("venue", MessageSegment, MessageSegment.venue)
Poll = SegmentPattern("poll", MessageSegment, MessageSegment.poll)
Dice = SegmentPattern("dice", MessageSegment, MessageSegment.dice)
ChatAction = SegmentPattern("chat_action", MessageSegment, MessageSegment.chat_action)

Mention = SegmentPattern("mention", Entity, Entity.mention)
Hashtag = SegmentPattern("hashtag", Entity, Entity.hashtag)
Cashtag = SegmentPattern("cashtag", Entity, Entity.cashtag)
BotCommand = TextSegmentPattern("bot_command", Entity, Entity.bot_command, locator)
Url = SegmentPattern("url", Entity, Entity.url)
Email = SegmentPattern("email", Entity, Entity.email)
PhoneNumber = SegmentPattern("phone_number", Entity, Entity.phone_number)
Bold = TextSegmentPattern("bold", Entity, Entity.bold, locator)
Italic = TextSegmentPattern("italic", Entity, Entity.italic, locator)
Underline = TextSegmentPattern("underline", Entity, Entity.underline, locator)
Strikethrough = TextSegmentPattern(
    "strikethrough", Entity, Entity.strikethrough, locator
)
Spoiler = TextSegmentPattern("spoiler", Entity, Entity.spoiler, locator)
Code = TextSegmentPattern("code", Entity, Entity.code, locator)
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

Sticker = SegmentPattern("sticker", UnCombinFile, UnCombinFile.sticker)
VideoNote = SegmentPattern("video_note", UnCombinFile, UnCombinFile.video_note)

Mentions = UnionPattern([Mention, TextMention, TextLink])
"""联合接收 Mention, TextMention, TextLink, 不能用于发送"""

Videos = UnionPattern([Video, Animation])
"""联合接收 Video, Animation, 不能用于发送"""
