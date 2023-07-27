from contextlib import suppress
from contextvars import ContextVar
from typing_extensions import Self

from tarina import lang
from nepattern import UnionPattern
from arclet.alconna import Namespace, NullMessage, set_default_argv_type
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
        "bold",
        "italic",
        "underline",
        "strikethrough",
        "spoiler",
        "code",
    }


TMA: ContextVar["TelegramMessageArgv"] = ContextVar("TMA")


class TelegramMessageArgv(MessageArgv):
    style_record: dict
    style_index: int

    def __post_init__(self, namespace: Namespace):
        super().__post_init__(namespace)
        self.converter = lambda x: Message(x)
        self.style_record = {}
        self.style_index = 0

    def reset(self):
        super().reset()
        self.style_record = {}
        self.style_index = 0
        if token := self.__class__._cache.get(self.__class__, {}).get("token"):
            with suppress(KeyError, RuntimeError):
                TMA.reset(token)

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
        msg = str(data)
        self.__class__._cache.setdefault(self.__class__, {})["token"] = TMA.set(self)
        i = 0
        raw_data = self.raw_data
        for index, unit in enumerate(data):
            if is_text(unit):
                if not (text := unit.data["text"].strip()):
                    if not index or index == len(data) - 1:
                        continue
                    if not is_text(data[index - 1]) or not is_text(data[index + 1]):
                        continue
                    text = unit.data["text"]
                if unit.type == "text":
                    if index != len(data) - 1 and is_text(data[index + 1]):
                        raw_data.append(unit.data["text"])
                    else:
                        raw_data.append(text)
                else:
                    if raw_data and raw_data[-1].__class__ is str:
                        raw_data[-1] = f"{raw_data[-1]}{text}"
                        i -= 1
                    else:
                        raw_data.append(text)
                    start = msg.find(unit.data["text"], self.style_index)
                    self.style_index = start + len(unit.data["text"])
                    self.style_record[(start, self.style_index)] = unit.type
            else:
                raw_data.append(unit)
            i += 1
        if i < 1:
            raise NullMessage(lang.require("argv", "null_message").format(target=data))
        self.ndata = i
        self.bak_data = raw_data.copy()
        if self.message_cache:
            self.token = self.generate_token(raw_data)
        self.style_index = 0
        return self


def locator(x: str, t: str):
    argv = TMA.get()
    msg = str(argv.origin)
    start = msg.find(x, argv.style_index)
    if start == -1:
        return False
    end = argv.style_index = start + len(x)
    if (maybe := argv.style_record.get((start, end))) and maybe == t:
        return True
    return any(
        scale[0] <= start <= scale[1]
        and scale[0] <= end <= scale[1]
        and argv.style_record[scale] == t
        for scale in argv.style_record
    )


Bold = TextSegmentPattern("bold", Entity, Entity.bold, locator)
Italic = TextSegmentPattern("italic", Entity, Entity.italic, locator)
Underline = TextSegmentPattern("underline", Entity, Entity.underline, locator)
Strikethrough = TextSegmentPattern(
    "strikethrough", Entity, Entity.strikethrough, locator
)
Spoiler = TextSegmentPattern("spoiler", Entity, Entity.spoiler, locator)
Code = TextSegmentPattern("code", Entity, Entity.code, locator)


set_default_argv_type(TelegramMessageArgv)

Text = str
Location = SegmentPattern("location", MessageSegment, MessageSegment.location)
Venue = SegmentPattern("venue", MessageSegment, MessageSegment.venue)
Poll = SegmentPattern("poll", MessageSegment, MessageSegment.poll)
Dice = SegmentPattern("dice", MessageSegment, MessageSegment.dice)
ChatAction = SegmentPattern("chat_action", MessageSegment, MessageSegment.chat_action)

Mention = SegmentPattern("mention", Entity, Entity.mention)
Hashtag = SegmentPattern("hashtag", Entity, Entity.hashtag)
Cashtag = SegmentPattern("cashtag", Entity, Entity.cashtag)
BotCommand = SegmentPattern("bot_command", Entity, Entity.bot_command)
Url = SegmentPattern("url", Entity, Entity.url)
Email = SegmentPattern("email", Entity, Entity.email)
PhoneNumber = SegmentPattern("phone_number", Entity, Entity.phone_number)

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
