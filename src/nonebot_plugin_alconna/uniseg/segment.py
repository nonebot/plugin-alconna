"""通用标注, 无法用于创建 MS对象"""
import re
import json
import contextlib
from pathlib import Path
from dataclasses import field, dataclass
from typing import TYPE_CHECKING, Any, Type, Union, Generic, Literal, TypeVar, Callable, Iterable, Optional

from nonebot.internal.adapter import Message, MessageSegment
from nepattern import MatchMode, BasePattern, create_local_patterns

if TYPE_CHECKING:
    from .message import UniMessage


TS = TypeVar("TS", bound="Segment")
TS1 = TypeVar("TS1", bound="Segment")


class UniPattern(BasePattern[TS], Generic[TS]):
    additional: Optional[Callable[..., bool]] = None

    def __init__(self):
        origin: Type[TS] = self.__class__.__orig_bases__[0].__args__[0]  # type: ignore

        def _converter(_, seg: MessageSegment) -> Optional[TS]:
            if (res := self.solve(seg)) and not hasattr(res, "origin"):
                res.origin = seg
            return res

        super().__init__(
            model=MatchMode.TYPE_CONVERT,
            origin=origin,
            converter=_converter,  # type: ignore
            alias=origin.__name__,
            accepts=[MessageSegment],
            validators=[self.additional] if self.additional else [],
        )

    def solve(self, seg: MessageSegment) -> Optional[TS]:
        raise NotImplementedError


@dataclass
class Segment:
    """基类标注"""

    origin: MessageSegment = field(init=False, repr=False, compare=False)

    def __str__(self):
        return f"[{self.__class__.__name__.lower()}]"

    def __add__(self: TS, item: Union[TS1, Iterable[TS1]]) -> "UniMessage[Union[TS, TS1]]":
        from .message import UniMessage

        return UniMessage(self) + item

    def __radd__(self: TS, item: Union[TS1, Iterable[TS1]]) -> "UniMessage[Union[TS, TS1]]":
        from .message import UniMessage

        return UniMessage(item) + self

    def is_text(self) -> bool:
        return False

    @property
    def type(self) -> str:
        return self.__class__.__name__.lower()


@dataclass
class Text(Segment):
    """Text对象, 表示一类文本元素"""

    text: str
    style: Optional[str] = field(default=None)

    def __post_init__(self):
        self.text = str(self.text)

    def is_text(self) -> bool:
        return True

    def __str__(self):
        return self.text


@dataclass
class At(Segment):
    """At对象, 表示一类提醒某用户的元素"""

    flag: Literal["user", "role", "channel"]
    target: str
    display: Optional[str] = field(default=None)


@dataclass
class AtAll(Segment):
    """AtAll对象, 表示一类提醒所有人的元素"""


@dataclass
class Emoji(Segment):
    """Emoji对象, 表示一类表情元素"""

    id: str
    name: Optional[str] = field(default=None)


@dataclass
class Media(Segment):
    url: Optional[str] = field(default=None)
    id: Optional[str] = field(default=None)
    path: Optional[Union[str, Path]] = field(default=None)
    raw: Optional[bytes] = field(default=None)
    name: Optional[str] = field(default=None)

    def __post_init__(self):
        if self.path:
            self.name = Path(self.path).name


@dataclass
class Image(Media):
    """Image对象, 表示一类图片元素"""

    name: str = field(default="image.png")


@dataclass
class Audio(Media):
    """Audio对象, 表示一类音频元素"""

    name: str = field(default="audio.mp3")


@dataclass
class Voice(Media):
    """Voice对象, 表示一类语音元素"""

    name: str = field(default="voice.wav")


@dataclass
class Video(Media):
    """Video对象, 表示一类视频元素"""

    name: str = field(default="video.mp4")


@dataclass
class File(Segment):
    """File对象, 表示一类文件元素"""

    id: Optional[str] = field(default=None)
    name: Optional[str] = field(default=None)
    raw: Optional[bytes] = field(default=None)


@dataclass
class Reply(Segment):
    """Reply对象，表示一类回复消息"""

    origin: Any
    id: str
    """此处不一定是消息ID，可能是其他ID，如消息序号等"""
    msg: Optional[Union[Message, str]] = field(default=None)


@dataclass
class Card(Segment):
    """Card对象，表示一类卡片消息"""

    flag: Literal["xml", "json"]
    raw: str
    content: Optional[Union[dict, list]] = field(default=None)

    def __post_init__(self):
        with contextlib.suppress(json.JSONDecodeError):
            self.content = json.loads(self.raw)


@dataclass
class Other(Segment):
    """其他 Segment"""

    origin: MessageSegment

    def __str__(self):
        return f"[{self.origin.type}]"


class _Other(UniPattern[Other]):
    def solve(self, seg: MessageSegment):
        return Other(seg)


other = _Other()


class _Text(UniPattern[Text]):
    def solve(self, seg: MessageSegment):
        if seg.is_text():
            return Text(seg.data["text"], seg.type if seg.type != "text" else None)


text = _Text()


class _At(UniPattern[At]):
    def solve(self, seg: MessageSegment):
        if seg.type == "at":  # ob11, feishu, red
            if "qq" in seg.data and seg.data["qq"] != "all":
                return At("user", str(seg.data["qq"]))
            if "user_id" in seg.data:
                return At("user", str(seg.data["user_id"]))
        if seg.type == "mention":  # ob12, tg
            if "user_id" in seg.data:
                return At("user", str(seg.data["user_id"]))
            if "text" in seg.data:
                return At("user", seg.data["text"])
        if seg.type == "mention_user":  # qqguild, discord, villa
            if "user_id" in seg.data:
                return At("user", str(seg.data["user_id"]))
            if "mention_user" in seg.data:
                return At("user", str(seg.data["mention_user"].user_id))
        if seg.type == "mention_channel":  # discord, qqguild
            return At("channel", str(seg.data["channel_id"]))
        if seg.type == "mention_role":  # discord
            return At("role", str(seg.data["role_id"]))
        if seg.type == "mention_robot":  # villa
            return At("user", str(seg.data["mention_robot"].bot_id))
        if seg.type == "At":  # mirai
            return At("user", str(seg.data["target"]))
        if seg.type == "kmarkdown":  # kook
            content = seg.data["content"]
            if not content.startswith("(met)"):
                return None
            if (end := content.find("(met)", 5)) == -1:
                return None
            return content[5:end] not in ("here", "all") and At("user", content[5:end])
        if seg.type == "room_link":  # villa
            return At(
                "channel",
                f'{seg.data["room_link"].villa_id}:{seg.data["room_link"].room_id}',
            )


at = _At()


class _AtAll(UniPattern[AtAll]):
    def solve(self, seg: MessageSegment):
        if seg.type == "at" and ("qq" in seg.data and seg.data["qq"] == "all"):
            return AtAll()
        if seg.type in {"at_all", "AtAll", "mention_everyone", "mention_all"}:
            return AtAll()
        if seg.type == "kmarkdown":
            content = seg.data["content"]
            if not content.startswith("(met)"):
                return None
            if (end := content.find("(met)", 5)) == -1:
                return None
            return content[5:end] in ("here", "all") and AtAll()


at_all = _AtAll()


class _Emoji(UniPattern[Emoji]):
    def solve(self, seg: MessageSegment):
        if seg.type == "emoji":
            if "id" in seg.data:
                return Emoji(seg.data["id"])
            if "name" in seg.data:
                return Emoji(seg.data["name"])
        if seg.type == "Face":
            return Emoji(str(seg.data["faceId"]), seg.data["name"])
        if seg.type == "face":
            if "id" in seg.data:
                return Emoji(str(seg.data["id"]))
            if "face_id" in seg.data:
                return Emoji(str(seg.data["face_id"]))
        if seg.type == "custom_emoji":
            if "custom_emoji_id" in seg.data:  # telegram
                return Emoji(seg.data["custom_emoji_id"], seg.data["text"])
            if "id" in seg.data:  # discord
                return Emoji(seg.data["id"], seg.data["name"])
        if seg.type == "kmarkdown":
            content = seg.data["content"]
            if content.startswith("(emj)"):
                mat = re.search(r"\(emj\)(?P<name>[^()\[\]]+)\(emj\)\[(?P<id>[^\[\]]+)\]", content)
                return mat and Emoji(mat["id"], mat["name"])
            if content.startswith(":"):
                mat = re.search(r":(?P<id>[^:]+):", content)
                return mat and Emoji(mat["id"])
        if seg.type == "sticker" and "id" in seg.data:
            return Emoji(seg.data["id"])


emoji = _Emoji()


class _Image(UniPattern[Image]):
    def solve(self, seg: MessageSegment):
        if seg.type == "image":
            if "uuid" in seg.data:  # red
                return Image(
                    id=seg.data["uuid"],
                    url=f"https://gchat.qpic.cn/gchatpic_new/0/0-0-{seg.data['md5'].upper()}/0",
                    path=seg.data["path"],
                    name=seg.data["md5"],
                )
            if "file_id" in seg.data:  # ob12
                return Image(id=seg.data["file_id"])
            if "image" in seg.data:  # villa
                return Image(url=seg.data["image"].url)
            if "image_key" in seg.data:  # feishu
                return Image(id=seg.data["image_key"])
            if "file_key" in seg.data:  # kook
                return Image(url=seg.data["file_key"])
            if "url" in seg.data:  # ob11
                return Image(url=seg.data["url"], id=seg.data["file"])
            if "msgData" in seg.data:  # minecraft
                return Image(url=seg.data["msgData"])
            if "file_path" in seg.data:  # ntchat
                return Image(id=seg.data["file_path"], path=seg.data["file_path"])
            if "picURL" in seg.data:  # ding
                return Image(url=seg.data["picURL"])
        if seg.type == "photo":
            return Image(id=seg.data["file"])
        if seg.type == "attachment":
            if "url" in seg.data:
                return Image(url=seg.data["url"])
            if "attachment" in seg.data:  # discord
                return Image(id=seg.data["attachment"].filename)
        if seg.type == "Image":
            return Image(seg.data["url"], seg.data["imageId"])


image = _Image()


class _Video(UniPattern[Video]):
    def solve(self, seg: MessageSegment):
        if seg.type == "video":
            if "videoMd5" in seg.data:  # red
                return Video(
                    id=seg.data["videoMd5"],
                    path=seg.data["filePath"],
                    name=seg.data["fileName"],
                )
            if "file_id" in seg.data:  # ob12, telegram
                return Video(id=seg.data["file_id"])
            if "file" in seg.data:  # ob11
                return Video(url=seg.data["file"])
            if "file_key" in seg.data:  # kook
                return Video(url=seg.data["file_key"])
            if "msgData" in seg.data:  # minecraft
                return Video(url=seg.data["msgData"])
            if "file_path" in seg.data:  # ntchat
                return Video(id=seg.data["file_path"], path=seg.data["file_path"])
        if seg.type == "video":
            return Video(seg.data["url"], seg.data["videoId"])
        if seg.type == "animation":
            return Video(id=seg.data["file_id"])
        if seg.type == "media":  # feishu
            return Video(id=seg.data["file_key"], name=seg.data["file_name"])


video = _Video()


class _Voice(UniPattern[Voice]):
    def solve(self, seg: MessageSegment):
        if seg.type == "voice":
            if "md5" in seg.data:  # red
                return Voice(
                    id=seg.data["md5"],
                    path=seg.data["path"],
                    name=seg.data["name"],
                )
            if "file_id" in seg.data:  # ob12, telegram
                return Voice(id=seg.data["file_id"])
            if "file_key" in seg.data:  # kook
                return Voice(url=seg.data["file_key"])
            if "file_path" in seg.data:  # ntchat
                return Voice(id=seg.data["file_path"], path=seg.data["file_path"])
        if seg.type == "record":
            return Voice(seg.data["url"])
        if seg.type == "Voice":
            return Voice(seg.data["url"], seg.data["voiceId"])


voice = _Voice()


class _Audio(UniPattern[Audio]):
    def solve(self, seg: MessageSegment):
        if seg.type != "audio":
            return
        if "file_id" in seg.data:  # ob12, telegram
            return Audio(id=seg.data["file_id"])
        if "file_key" in seg.data:  # kook, feishu
            return Audio(url=seg.data["file_key"])
        if "file_path" in seg.data:  # ntchat
            return Audio(id=seg.data["file_path"], path=seg.data["file_path"])


audio = _Audio()


class _File(UniPattern[File]):
    def solve(self, seg: MessageSegment):
        if seg.type == "file":
            if "md5" in seg.data:  # red
                return File(
                    id=seg.data["md5"],
                    name=seg.data["name"],
                )
            if "file_id" in seg.data:  # ob12
                return File(id=seg.data["file_id"])
            if "file_key" in seg.data:  # feishu, kook
                return File(
                    id=seg.data["file_key"],
                    name=seg.data.get("file_name", seg.data.get("title")),
                )
            if "file_path" in seg.data:  # ntchat
                return File(id=seg.data["file_path"])
        if seg.type == "document":
            return File(seg.data["file_id"], seg.data["file_name"])
        if seg.type == "File":
            return File(seg.data["id"], seg.data["name"])


file = _File()


class _Reply(UniPattern[Reply]):
    def solve(self, seg: MessageSegment):
        if seg.type == "reference":
            if "message_id" in seg.data:  # telegram
                return Reply(seg, seg.data["message_id"])
            if "reference" in seg.data:  # discord
                return Reply(seg, seg.data["reference"].message_id)
        if seg.type == "reply":
            if "id" in seg.data:  # ob11
                return Reply(seg, seg.data["id"])
            if "message_id" in seg.data:  # ob12
                return Reply(seg, seg.data["message_id"])
            if "msg_id" in seg.data:  # red
                return Reply(seg.data["_origin"], seg.data["msg_seq"])
        if seg.type == "quote":
            if "msg_id" in seg.data:  # kook:
                return Reply(seg, seg.data["msg_id"])
            if "quoted_message_id" in seg.data:  # villa
                return Reply(seg, seg.data["quoted_message_id"])
        if seg.type == "Quote":  # mirai
            return Reply(seg, str(seg.data["id"]), str(seg.data["origin"]))


reply = _Reply()


class _Card(UniPattern[Card]):
    def solve(self, seg: MessageSegment):
        if seg.type == "card":
            if "content" in seg.data:  # kook
                return Card("json", seg.data["content"])
            if "card_wxid" in seg.data:  # ntchat
                return Card("json", seg.data["card_wxid"])
        if seg.type == "Xml":  # mirai
            return Card("xml", seg.data["xml"])
        if seg.type == "Json":  # mirai
            return Card("json", seg.data["json"])
        if seg.type == "App":  # mirai
            return Card("json", seg.data["content"])
        if seg.type == "xml":  # ob12
            return Card("xml", seg.data["data"])
        if seg.type == "json":  # ob11
            return Card("json", seg.data["data"])
        if seg.type == "ark" and "data" in seg.data:  # red
            return Card("json", seg.data["data"])


card = _Card()
segments = [at, at_all, emoji, image, video, voice, audio, file, card, text, other]
env = create_local_patterns("nonebot")
env.sets(segments)


class _Segment(UniPattern[Segment]):
    def solve(self, seg: MessageSegment):
        for pat in segments:
            if (res := pat.validate(seg)).success:
                return res.value
        return Other(seg)  # type: ignore


env[Segment] = _Segment()
