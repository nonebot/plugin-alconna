"""通用标注, 无法用于创建 MS对象"""
import re
import json
import contextlib
from io import BytesIO
from pathlib import Path
from base64 import b64decode
from datetime import datetime
from urllib.parse import urlparse
from dataclasses import field, asdict, dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Type,
    Union,
    Generic,
    Literal,
    TypeVar,
    Callable,
    Iterable,
    Optional,
    overload,
)

import fleep
from nepattern import MatchMode, BasePattern, create_local_patterns
from nonebot.internal.adapter import Bot, Event, Message, MessageSegment

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


class Segment:
    """基类标注"""

    if TYPE_CHECKING:
        origin: MessageSegment  # = field(init=False, repr=False, compare=False)

    def __str__(self):
        return f"[{self.__class__.__name__.lower()}]"

    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.data.items())
        return f"{self.__class__.__name__}({attrs})"

    @overload
    def __add__(self: TS, item: str) -> "UniMessage[Union[TS, Text]]":
        ...

    @overload
    def __add__(self: TS, item: Union[TS, Iterable[TS]]) -> "UniMessage[TS]":
        ...

    @overload
    def __add__(self: TS, item: Union[TS1, Iterable[TS1]]) -> "UniMessage[Union[TS, TS1]]":
        ...

    def __add__(self: TS, item: Union[str, Union[TS, TS1], Iterable[Union[TS, TS1]]]) -> "UniMessage":
        from .message import UniMessage

        return UniMessage(self) + item

    @overload
    def __radd__(self: TS, item: str) -> "UniMessage[Union[Text, TS]]":
        ...

    @overload
    def __radd__(self: TS, item: Union[TS, Iterable[TS]]) -> "UniMessage[TS]":
        ...

    @overload
    def __radd__(self: TS, item: Union[TS1, Iterable[TS1]]) -> "UniMessage[Union[TS1, TS]]":
        ...

    def __radd__(self: TS, item: Union[str, Union[TS, TS1], Iterable[Union[TS, TS1]]]) -> "UniMessage":
        from .message import UniMessage

        return UniMessage(item) + self

    def is_text(self) -> bool:
        return False

    @property
    def type(self) -> str:
        return self.__class__.__name__.lower()

    @property
    def data(self) -> Dict[str, Any]:
        try:
            return asdict(self)  # type: ignore
        except TypeError:
            return vars(self)


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

    here: bool = field(default=False)


@dataclass
class Emoji(Segment):
    """Emoji对象, 表示一类表情元素"""

    id: str
    name: Optional[str] = field(default=None)


@dataclass
class Media(Segment):
    id: Optional[str] = field(default=None)
    url: Optional[str] = field(default=None)
    path: Optional[Union[str, Path]] = field(default=None)
    raw: Optional[Union[bytes, BytesIO]] = field(default=None)
    mimetype: Optional[str] = field(default=None)
    name: Optional[str] = field(default=None)

    def __post_init__(self):
        if self.path:
            self.name = Path(self.path).name
        if self.url and not urlparse(self.url).hostname:
            self.url = f"https://{self.url}"

    @property
    def raw_bytes(self) -> bytes:
        if not self.raw:
            raise ValueError(f"{self} has no raw data")
        raw = self.raw.getvalue() if isinstance(self.raw, BytesIO) else self.raw
        header = raw[:128]
        info = fleep.get(header)
        self.mimetype = info.mime[0] if info.mime else self.mimetype
        if info.type and info.extension:
            self.name = f"{info.type[0]}.{info.extension[0]}"
        return raw


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
class File(Media):
    """File对象, 表示一类文件元素"""

    name: str = field(default="file.bin")


@dataclass
class Reply(Segment):
    """Reply对象，表示一类回复消息"""

    id: str
    """此处不一定是消息ID，可能是其他ID，如消息序号等"""
    msg: Optional[Union[Message, str]] = field(default=None)
    origin: Optional[Any] = field(default=None)


@dataclass
class RefNode:
    """表示转发消息的引用消息元素"""

    id: str
    context: Optional[str] = None


@dataclass
class CustomNode:
    """表示转发消息的自定义消息元素"""

    uid: str
    name: str
    time: datetime
    content: Union[str, List[Segment], Message]


@dataclass
class Reference(Segment):
    """Reference对象，表示一类引用消息。转发消息 (Forward) 也属于此类"""

    id: Optional[str] = field(default=None)
    """此处不一定是消息ID，可能是其他ID，如消息序号等"""
    content: Optional[Union[Message, str, List[Union[RefNode, CustomNode]]]] = field(default=None)


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
        if seg.type == "markdown":  # qq, console
            if "markup" in seg.data:  # console
                return Text(seg.data["markup"], "markdown")
            return Text(seg.data["content"], "markdown")
        if seg.type == "markup":  # console
            return Text(seg.data["markup"], "markup")
        if seg.type == "kmarkdown":  # kook
            return Text(seg.data["content"], "markdown")
        if seg.is_text():
            return Text(seg.data["text"], seg.type if seg.type != "text" else None)


text = _Text()


class _At(UniPattern[At]):
    def solve(self, seg: MessageSegment):
        if seg.type == "at":  # ob11, feishu, red, satori, kook(edited)
            if "qq" in seg.data and seg.data["qq"] != "all":
                return At("user", str(seg.data["qq"]))
            if "user_id" in seg.data and seg.data["user_id"] not in ("all", "here"):
                return At("user", str(seg.data["user_id"]))
            if "id" in seg.data:
                return At("user", seg.data["id"], seg.data["name"])
            if "role" in seg.data:
                return At("role", seg.data["role"], seg.data["name"])
        if seg.type == "at_user":  # dodo
            return At("user", seg.data["dodo_id"])
        if seg.type == "at_role":  # dodo, kook(edited)
            return At("role", seg.data["role_id"])
        if seg.type == "at_channel":  # kook(edited)
            return At("channel", seg.data["channel_id"])
        if seg.type == "channel_link":  # dodo
            return At("channel", seg.data["channel_id"])
        if seg.type == "sharp":  # satori
            return At("channel", seg.data["channel_id"], seg.data["name"])
        if seg.type == "mention":
            if "user_id" in seg.data:  # ob12
                return At("user", str(seg.data["user_id"]))
            if "text" in seg.data:  # tg
                return At("user", seg.data["text"])
        if seg.type == "text_mention":  # tg
            return At("user", str(seg.data["user"].id), seg.data["text"])
        if seg.type == "mention_user":
            if "user_id" in seg.data:  # qq, qqguild, discord
                return At("user", str(seg.data["user_id"]))
            if "mention_user" in seg.data:  # villa
                return At("user", str(seg.data["mention_user"].user_id), seg.data["mention_user"].user_name)
        if seg.type == "mention_channel":  # discord, qq, qqguild
            return At("channel", str(seg.data["channel_id"]))
        if seg.type == "mention_role":  # discord
            return At("role", str(seg.data["role_id"]))
        if seg.type == "mention_robot":  # villa
            return At("user", str(seg.data["mention_robot"].bot_id), seg.data["mention_robot"].bot_name)
        if seg.type == "At":  # mirai
            return At("user", str(seg.data["target"]), seg.data["display"])
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
                seg.data["room_link"].room_name,
            )


at = _At()


class _AtAll(UniPattern[AtAll]):
    def solve(self, seg: MessageSegment):
        if seg.type == "at":
            if "qq" in seg.data and seg.data["qq"] == "all":  # ob11
                return AtAll()
            if "user_id" in seg.data and seg.data["user_id"] in ("all", "here"):  # feishu, kook(edited)
                return AtAll()
            if "type" in seg.data and seg.data["type"] in ("all", "here"):  # satori
                return AtAll(here=seg.data["type"] == "here")
        if seg.type in {"at_all", "AtAll", "mention_everyone", "mention_all"}:
            return AtAll()
        if seg.type == "kmarkdown":
            content = seg.data["content"]
            if not content.startswith("(met)"):
                return None
            if (end := content.find("(met)", 5)) == -1:
                return None
            return content[5:end] in ("here", "all") and AtAll(content[5:end] == "here")


at_all = _AtAll()


class _Emoji(UniPattern[Emoji]):
    def solve(self, seg: MessageSegment):
        if seg.type == "emoji":
            if "id" in seg.data:
                if "name" in seg.data:
                    return Emoji(seg.data["id"], seg.data["name"])
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
        if seg.type == "kmarkdown":  # kook
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
            if "url" in seg.data:  # ob11, qq
                if "filename" in seg.data:
                    return Image(
                        url=seg.data["url"],
                        id=seg.data["filename"],
                        mimetype=seg.data["content_type"],
                        name=seg.data["filename"],
                    )
                if "file" in seg.data:
                    return Image(url=seg.data["url"], id=seg.data["file"])
                return Image(url=seg.data["url"])
            if "msgData" in seg.data:  # minecraft
                return Image(url=seg.data["msgData"])
            if "file_path" in seg.data:  # ntchat
                return Image(id=seg.data["file_path"], path=seg.data["file_path"])
            if "picURL" in seg.data:  # ding
                return Image(url=seg.data["picURL"])
        if seg.type == "photo":  # tg
            return Image(id=seg.data["file"])
        if seg.type == "attachment":
            if "url" in seg.data:  # qqguild
                return Image(url=seg.data["url"])
            if "attachment" in seg.data:  # discord
                return Image(id=seg.data["attachment"].filename)
        if seg.type == "picture":  # dodo
            return Image(url=seg.data["picture"].url)
        if seg.type == "Image":  # mirai
            return Image(url=seg.data["url"], id=seg.data["imageId"])
        if seg.type == "img":  # satori
            src = seg.data["src"]
            if src.startswith("http"):
                return Image(url=src)
            if src.startswith("file://"):
                return Image(path=Path(src[7:]))
            if src.startswith("data:"):
                mime, b64 = src[5:].split(";", 1)
                return Image(raw=b64decode(b64[7:]), mimetype=mime)
            return Image(seg.data["src"])


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
            if "video" in seg.data:  # dodo
                return Video(url=seg.data["video"].url)
            if "file_id" in seg.data:  # ob12, telegram
                return Video(id=seg.data["file_id"])
            if "file" in seg.data:  # ob11
                return Video(url=seg.data["file"])
            if "url" in seg.data:  # qq
                if "filename" in seg.data:
                    return Video(
                        url=seg.data["url"],
                        id=seg.data["filename"],
                        mimetype=seg.data["content_type"],
                        name=seg.data["filename"],
                    )
                return Video(url=seg.data["url"])
            if "file_key" in seg.data:  # kook
                return Video(url=seg.data["file_key"])
            if "msgData" in seg.data:  # minecraft
                return Video(url=seg.data["msgData"])
            if "file_path" in seg.data:  # ntchat
                return Video(id=seg.data["file_path"], path=seg.data["file_path"])
            if "src" in seg.data:  # satori
                src = seg.data["src"]
                if src.startswith("http"):
                    return Video(url=src)
                if src.startswith("file://"):
                    return Video(path=Path(src[7:]))
                if src.startswith("data:"):
                    mime, b64 = src[5:].split(";", 1)
                    return Video(raw=b64decode(b64[7:]), mimetype=mime)
                return Video(seg.data["src"])
        if seg.type == "Video":  # mirai
            return Video(url=seg.data["url"], id=seg.data["videoId"])
        if seg.type == "animation":  # telegram
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
        if seg.type == "record":  # ob11
            return Voice(url=seg.data["url"])
        if seg.type == "Voice":  # mirai
            return Voice(url=seg.data["url"], id=seg.data["voiceId"])


voice = _Voice()


class _Audio(UniPattern[Audio]):
    def solve(self, seg: MessageSegment):
        if seg.type != "audio":
            return
        if "url" in seg.data:  # qq
            if "filename" in seg.data:
                return Audio(
                    url=seg.data["url"],
                    id=seg.data["filename"],
                    mimetype=seg.data["content_type"],
                    name=seg.data["filename"],
                )
            return Audio(url=seg.data["url"])
        if "file_id" in seg.data:  # ob12, telegram
            return Audio(id=seg.data["file_id"])
        if "file_key" in seg.data:  # kook, feishu
            return Audio(url=seg.data["file_key"])
        if "file_path" in seg.data:  # ntchat
            return Audio(id=seg.data["file_path"], path=seg.data["file_path"])
        if "src" in seg.data:  # satori
            src = seg.data["src"]
            if src.startswith("http"):
                return Audio(url=src)
            if src.startswith("file://"):
                return Audio(path=Path(src[7:]))
            if src.startswith("data:"):
                mime, b64 = src[5:].split(";", 1)
                return Audio(raw=b64decode(b64[7:]), mimetype=mime)
            return Audio(seg.data["src"])


audio = _Audio()


class _File(UniPattern[File]):
    def solve(self, seg: MessageSegment):
        if seg.type == "file":
            if "md5" in seg.data:  # red
                return File(
                    id=seg.data["md5"],
                    name=seg.data["name"],
                )
            if "url" in seg.data:  # qq
                if "filename" in seg.data:
                    return File(
                        url=seg.data["url"],
                        id=seg.data["filename"],
                        mimetype=seg.data["content_type"],
                        name=seg.data["filename"],
                    )
                return File(url=seg.data["url"])
            if "file" in seg.data:  # dodo
                return File(url=seg.data["file"].url)
            if "file_id" in seg.data:  # ob12
                return File(id=seg.data["file_id"])
            if "file_key" in seg.data:  # feishu, kook
                return File(
                    id=seg.data["file_key"],
                    name=seg.data.get("file_name", seg.data.get("title")),
                )
            if "file_path" in seg.data:  # ntchat
                return File(id=seg.data["file_path"])
            if "src" in seg.data:  # satori
                src = seg.data["src"]
                if src.startswith("http"):
                    return File(url=src)
                if src.startswith("file://"):
                    return File(path=Path(src[7:]))
                if src.startswith("data:"):
                    mime, b64 = src[5:].split(";", 1)
                    return File(raw=b64decode(b64[7:]), mimetype=mime)
                return File(seg.data["src"])
        if seg.type == "document":  # telegram
            return File(seg.data["file_id"], name=seg.data["file_name"])
        if seg.type == "File":  # mirai
            return File(seg.data["id"], name=seg.data["name"])


file = _File()


class _Reply(UniPattern[Reply]):
    def solve(self, seg: MessageSegment):
        if seg.type == "reference":
            if "message_id" in seg.data:  # telegram, dodo
                return Reply(seg.data["message_id"], origin=seg)
            if "reference" in seg.data:  # discord, qq, qqguild
                return Reply(seg.data["reference"].message_id, origin=seg.data["reference"])
        if seg.type == "reply":
            if "id" in seg.data:  # ob11
                return Reply(seg.data["id"], origin=seg)
            if "message_id" in seg.data:  # ob12
                return Reply(seg.data["message_id"], origin=seg)
            if "msg_id" in seg.data:  # red
                return Reply(seg.data["msg_seq"], origin=seg.data["_origin"])
        if seg.type == "quote":
            if "id" in seg.data:  # satori
                return Reply(seg.data["id"], seg.data.get("content"), seg)
            if "msg_id" in seg.data:  # kook:
                return Reply(seg.data["msg_id"], origin=seg)
            if "quoted_message_id" in seg.data:  # villa
                return Reply(seg.data["quote"].quoted_message_id, origin=seg.data["quote"])
        if seg.type == "Quote":  # mirai
            return Reply(str(seg.data["id"]), seg.data["origin"], origin=seg)


reply = _Reply()


class _Reference(UniPattern[Reference]):
    def solve(self, seg: MessageSegment):
        if seg.type == "post":  # villa
            return Reference(seg.data["post"].post_id)
        if seg.type == "message":  # satori
            return Reference(seg.data.get("id"), seg.data.get("content"))
        if seg.type == "forward":
            if "xml" in seg.data:  # red
                return Reference(seg.data["id"], seg.data["xml"])
            return Reference(seg.data["id"])  # ob11
        if seg.type == "Forward":  # mirai
            nodes = []
            for node in seg.data["nodeList"]:
                if "messageId" in node:
                    nodes.append(RefNode(node["messageId"]))
                elif "messageRef" in node:
                    nodes.append(RefNode(node["messageRef"]["messageId"], node["messageRef"]["target"]))
                else:
                    nodes.append(
                        CustomNode(node["senderId"], node["senderName"], node["time"], node["messageChain"])
                    )
            return Reference(seg.data.get("messageId"), nodes)


reference = _Reference()


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
segments = [at_all, at, emoji, image, video, voice, audio, file, reference, card, text, other]
env = create_local_patterns("nonebot")
env.sets(segments)


class _Segment(UniPattern[Segment]):
    def solve(self, seg: MessageSegment):
        for pat in segments:
            if (res := pat.validate(seg)).success:
                res.value.origin = seg
                return res.value
        return Other(seg)  # type: ignore


env[Segment] = _Segment()


async def reply_handle(event: Event, bot: Bot):
    adapter = bot.adapter
    adapter_name = adapter.get_name()
    if adapter_name == "Telegram":
        if TYPE_CHECKING:
            from nonebot.adapters.telegram.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.reply_to_message:
            return Reply(
                f"{event.reply_to_message.message_id}",
                event.reply_to_message.original_message,
                event.reply_to_message,
            )
    elif adapter_name == "Feishu":
        if TYPE_CHECKING:
            from nonebot.adapters.feishu.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.reply:
            return Reply(event.reply.message_id, event.reply.body.content, event.reply)
    elif adapter_name == "ntchat":
        if TYPE_CHECKING:
            from nonebot.adapters.ntchat.event import QuoteMessageEvent

            assert isinstance(event, QuoteMessageEvent)
        if event.type == 11061:
            return Reply(event.quote_message_id, origin=event)
    elif adapter_name == "QQ Guild":
        if TYPE_CHECKING:
            from nonebot.adapters.qqguild.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.reply and event.reply.message:
            return Reply(
                str(event.reply.message.id),
                event.reply.message.content,
                event.reply.message,
            )
    elif adapter_name == "QQ":
        if TYPE_CHECKING:
            from nonebot.adapters.qq.event import GuildMessageEvent

            assert isinstance(event, GuildMessageEvent)
        if hasattr(event, "reply") and event.reply:
            return Reply(
                str(event.reply.id),
                event.reply.content,
                event.reply,
            )
    elif adapter_name == "Satori":
        if TYPE_CHECKING:
            from nonebot.adapters.satori.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.reply:
            return Reply(
                str(event.reply.data.get("id")),
                event.reply.data.get("content"),
                event.reply,
            )
    elif adapter_name == "mirai2":
        if TYPE_CHECKING:
            from nonebot.adapters.mirai2.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.quote:
            return Reply(str(event.quote.id), event.quote.origin, event.quote)
    elif adapter_name == "Kaiheila":
        if TYPE_CHECKING:
            from nonebot.adapters.kaiheila import Bot as KaiheilaBot
            from nonebot.adapters.kaiheila.event import MessageEvent

            assert isinstance(event, MessageEvent)
            assert isinstance(bot, KaiheilaBot)

        api = "directMessage_view" if event.__event__ == "message.private" else "message_view"
        message = await bot.call_api(
            api,
            msg_id=event.msg_id,
            **({"chat_code": event.event.code} if event.__event__ == "message.private" else {}),
        )
        if message.quote:
            return Reply(message.quote.id_, origin=message.quote)
    elif adapter_name == "Discord":
        if TYPE_CHECKING:
            from nonebot.adapters.discord import MessageEvent

            assert isinstance(event, MessageEvent)

        if hasattr(event, "message_reference") and hasattr(event.message_reference, "message_id"):
            return Reply(
                event.message_reference.message_id,  # type: ignore
                origin=event.message_reference,  # type: ignore
            )
    elif adapter_name == "RedProtocol":
        if TYPE_CHECKING:
            from nonebot.adapters.red.event import MessageEvent

            assert isinstance(event, MessageEvent)

        if event.reply:
            return Reply(
                f"{event.reply.sourceMsgIdInRecords}#{event.reply.replayMsgSeq}",
                event.reply.sourceMsgTextElems,
                origin=event.reply,
            )
    elif adapter_name == "Villa":
        if TYPE_CHECKING:
            from nonebot.adapters.villa.event import SendMessageEvent

            assert isinstance(event, SendMessageEvent)

        if event.quote_msg:
            return Reply(
                f"{event.quote_msg.msg_uid}@{event.quote_msg.send_at}",
                msg=event.quote_msg.content,
                origin=event.quote_msg,
            )
    elif _reply := getattr(event, "reply", None):
        return Reply(str(_reply.message_id), getattr(_reply, "message", None), _reply)
    return None
