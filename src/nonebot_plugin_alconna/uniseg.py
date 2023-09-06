"""通用标注, 无法用于创建 MS对象"""
import re
import json
import contextlib
from copy import deepcopy
from dataclasses import field, dataclass
from typing_extensions import Self, SupportsIndex
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Type,
    Tuple,
    Union,
    Literal,
    TypeVar,
    Optional,
    overload,
)

from nepattern import BasePattern, create_local_patterns
from nonebot.internal.adapter import Bot, Event, Message, MessageSegment

from .typings import UniPattern

Text = str


@dataclass
class Segment:
    """基类标注"""

    def __str__(self):
        return f"[{self.__class__.__name__.lower()}]"


@dataclass
class At(Segment):
    """At对象, 表示一类提醒某用户的元素"""

    type: Literal["user", "role", "channel"]
    target: str


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
    path: Optional[str] = field(default=None)
    raw: Optional[bytes] = field(default=None)


@dataclass
class Image(Media):
    """Image对象, 表示一类图片元素"""


@dataclass
class Audio(Media):
    """Audio对象, 表示一类音频元素"""


@dataclass
class Voice(Media):
    """Voice对象, 表示一类语音元素"""


@dataclass
class Video(Media):
    """Video对象, 表示一类视频元素"""


@dataclass
class File(Segment):
    """File对象, 表示一类文件元素"""

    id: str
    name: Optional[str] = field(default=None)


@dataclass
class Reply(Segment):
    """Reply对象，表示一类回复消息"""

    origin: Any
    id: str
    msg: Optional[Union[Message, str]] = field(default=None)


@dataclass
class Card(Segment):
    """Card对象，表示一类卡片消息"""

    raw: str
    content: Optional[dict] = field(default=None)

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
                mat = re.search(
                    r"\(emj\)(?P<name>[^()\[\]]+)\(emj\)\[(?P<id>[^\[\]]+)\]", content
                )
                return mat and Emoji(mat["id"], mat["name"])
            if content.startswith(":"):
                mat = re.search(r":(?P<name>[^:]+):", content)
                return mat and Emoji(mat["name"], mat["name"])
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
                )
            if "file_id" in seg.data:  # ob12
                return Image(id=seg.data["file_id"])
            if "image" in seg.data:  # villa
                return Image(url=seg.data["image"].url)
            if "image_key" in seg.data:  # feishu
                return Image(url=seg.data["image_key"])
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


video = _Video()


class _Voice(UniPattern[Voice]):
    def solve(self, seg: MessageSegment):
        if seg.type == "voice":
            if "md5" in seg.data:  # red
                return Voice(
                    id=seg.data["md5"],
                    path=seg.data["path"],
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
                return Reply(seg, seg.data["msg_id"])
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
            if "content" in seg.data:
                return Card(seg.data["content"])
            if "card_wxid" in seg.data:
                return Card(seg.data["card_wxid"])
        if seg.type == "Xml":
            return Card(seg.data["xml"])
        if seg.type == "Json":
            return Card(seg.data["json"])
        if seg.type == "App":
            return Card(seg.data["content"])
        if seg.type == "xml":
            return Card(seg.data["data"])
        if seg.type == "json":
            return Card(seg.data["data"])
        if seg.type == "ark" and "data" in seg.data:
            return Card(seg.data["data"])


card = _Card()

env = create_local_patterns("nonebot")
env.sets([at, at_all, image, voice, video, audio, emoji, file, reply, card, other])
env[Segment] = BasePattern.of(MessageSegment)

US = Union[Segment, str]
TS = TypeVar("TS", bound=US)


async def reply_handle(event: Event, bot: Bot):
    adapter = bot.adapter
    adapter_name = adapter.get_name()
    if adapter_name == "Telegram":
        if TYPE_CHECKING:
            from nonebot.adapters.telegram.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.reply_to_message:
            return Reply(
                event.reply_to_message,
                f"{event.reply_to_message.message_id}.{event.chat.id}",
                event.reply_to_message.original_message,
            )
    elif adapter_name == "Feishu":
        if TYPE_CHECKING:
            from nonebot.adapters.feishu.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.reply:
            return Reply(event.reply, event.reply.message_id, event.reply.body.content)
    elif adapter_name == "ntchat":
        if TYPE_CHECKING:
            from nonebot.adapters.ntchat.event import QuoteMessageEvent

            assert isinstance(event, QuoteMessageEvent)
        if event.type == 11061:
            return Reply(event, event.quote_message_id)
    elif adapter_name == "QQ Guild":
        if TYPE_CHECKING:
            from nonebot.adapters.qqguild.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.reply and event.reply.message:
            return Reply(
                event.reply.message,
                str(event.reply.message.id),
                event.reply.message.content,
            )
    elif adapter_name == "mirai2":
        if TYPE_CHECKING:
            from nonebot.adapters.mirai2.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.quote:
            return Reply(event.quote, str(event.quote.id), event.quote.origin)
    elif adapter_name == "Kaiheila":
        if TYPE_CHECKING:
            from nonebot.adapters.kaiheila import Bot as KaiheilaBot
            from nonebot.adapters.kaiheila.event import MessageEvent

            assert isinstance(event, MessageEvent)
            assert isinstance(bot, KaiheilaBot)

        api = (
            "directMessage_view"
            if event.__event__ == "message.private"
            else "message_view"
        )
        message = await bot.call_api(
            api,
            msg_id=event.msg_id,
            **(
                {"chat_code": event.event.code}
                if event.__event__ == "message.private"
                else {}
            ),
        )
        if message.quote:
            return Reply(message.quote, message.quote.id_, None)
    elif adapter_name == "Discord":
        if TYPE_CHECKING:
            from nonebot.adapters.discord import MessageEvent

            assert isinstance(event, MessageEvent)

        if hasattr(event, "message_reference") and hasattr(
            event.message_reference, "message_id"
        ):
            return Reply(
                event.message_reference, event.message_reference.message_id, None
            )

    elif _reply := getattr(event, "reply", None):
        return Reply(_reply, str(_reply.message_id), getattr(_reply, "message", None))
    return None


class UniMessage(List[US]):
    """通用消息序列

    参数:
        message: 消息内容
    """

    def __str__(self) -> str:
        return "".join(str(seg) for seg in self)

    def __repr__(self) -> str:
        return "".join(repr(seg) for seg in self)

    @overload
    def __getitem__(self, args: Type[TS]) -> "UniMessage[TS]":
        """获取仅包含指定消息段类型的消息

        参数:
            args: 消息段类型

        返回:
            所有类型为 `args` 的消息段
        """

    @overload
    def __getitem__(self, args: Tuple[Type[TS], int]) -> TS:
        """索引指定类型的消息段

        参数:
            args: 消息段类型和索引

        返回:
            类型为 `args[0]` 的消息段第 `args[1]` 个
        """

    @overload
    def __getitem__(self, args: Tuple[Type[TS], slice]) -> "UniMessage[TS]":
        """切片指定类型的消息段

        参数:
            args: 消息段类型和切片

        返回:
            类型为 `args[0]` 的消息段切片 `args[1]`
        """

    @overload
    def __getitem__(self, args: int) -> US:
        """索引消息段

        参数:
            args: 索引

        返回:
            第 `args` 个消息段
        """

    @overload
    def __getitem__(self, args: slice) -> Self:
        """切片消息段

        参数:
            args: 切片

        返回:
            消息切片 `args`
        """

    def __getitem__(
        self,
        args: Union[
            Type[US],
            Tuple[Type[US], int],
            Tuple[Type[US], slice],
            int,
            slice,
        ],
    ) -> Union[US, Self]:
        arg1, arg2 = args if isinstance(args, tuple) else (args, None)
        if isinstance(arg1, int) and arg2 is None:
            return super().__getitem__(arg1)
        elif isinstance(arg1, slice) and arg2 is None:
            return self.__class__(super().__getitem__(arg1))
        elif (arg1 in (str, Segment) or issubclass(arg1, Segment)) and arg2 is None:
            return self.__class__(seg for seg in self if isinstance(seg, arg1))
        elif (arg1 in (str, Segment) or issubclass(arg1, Segment)) and isinstance(
            arg2, int
        ):
            return [seg for seg in self if isinstance(seg, arg1)][arg2]
        elif (arg1 in (str, Segment) or issubclass(arg1, Segment)) and isinstance(
            arg2, slice
        ):
            return self.__class__([seg for seg in self if isinstance(seg, arg1)][arg2])
        else:
            raise ValueError("Incorrect arguments to slice")  # pragma: no cover

    def __contains__(self, value: Union[US, Type[US]]) -> bool:
        """检查消息段是否存在

        参数:
            value: 消息段或消息段类型
        返回:
            消息内是否存在给定消息段或给定类型的消息段
        """
        if value in (str, Segment) or issubclass(value, Segment):
            return bool(next((seg for seg in self if isinstance(seg, value)), None))
        return super().__contains__(value)

    def has(self, value: Union[US, Type[US]]) -> bool:
        """与 {ref}``__contains__` <nonebot.adapters.Message.__contains__>` 相同"""
        return value in self

    def index(self, value: Union[US, Type[US]], *args: SupportsIndex) -> int:
        """索引消息段

        参数:
            value: 消息段或者消息段类型
            arg: start 与 end

        返回:
            索引 index

        异常:
            ValueError: 消息段不存在
        """
        if value in (str, Segment) or issubclass(value, Segment):
            first_segment = next((seg for seg in self if isinstance(seg, value)), None)
            if first_segment is None:
                raise ValueError(f"Segment with type {value!r} is not in message")
            return super().index(first_segment, *args)
        return super().index(value, *args)

    def get(self, type_: Type[TS], count: Optional[int] = None) -> "UniMessage[TS]":
        """获取指定类型的消息段

        参数:
            type_: 消息段类型
            count: 获取个数

        返回:
            构建的新消息
        """
        if count is None:
            return self[type_]

        iterator, filtered = (
            seg for seg in self if isinstance(seg, type_)
        ), self.__class__()
        for _ in range(count):
            seg = next(iterator, None)
            if seg is None:
                break
            filtered.append(seg)
        return filtered

    def count(self, value: Union[Type[US], US]) -> int:
        """计算指定消息段的个数

        参数:
            value: 消息段或消息段类型

        返回:
            个数
        """
        return (
            len(self[value])
            if value in (str, Segment) or issubclass(value, Segment)
            else super().count(value)
        )

    def only(self, value: Union[Type[US], US]) -> bool:
        """检查消息中是否仅包含指定消息段

        参数:
            value: 指定消息段或消息段类型

        返回:
            是否仅包含指定消息段
        """
        if value in (str, Segment) or issubclass(value, Segment):
            return all(isinstance(seg, value) for seg in self)
        return all(seg == value for seg in self)

    def copy(self) -> Self:
        """深拷贝消息"""
        return deepcopy(self)

    def include(self, *types: Type[US]) -> Self:
        """过滤消息

        参数:
            types: 包含的消息段类型

        返回:
            新构造的消息
        """
        return self.__class__(seg for seg in self if seg.__class__ in types)

    def exclude(self, *types: Type[US]) -> Self:
        """过滤消息

        参数:
            types: 不包含的消息段类型

        返回:
            新构造的消息
        """
        return self.__class__(seg for seg in self if seg.__class__ not in types)

    def extract_plain_text(self) -> str:
        """提取消息内纯文本消息"""

        return "".join(seg for seg in self if seg.__class__ is str)

    @classmethod
    async def generate(cls, event: Event, bot: Bot):
        try:
            msg = event.get_message()
        except Exception:
            return cls()
        result = cls()
        msg_copy = msg.copy()
        if _reply := await reply_handle(event, bot):
            result.append(_reply)
        elif (res := reply.validate(msg[0])).success:
            result.append(res.value)
            msg_copy.pop(0)
        for seg in msg_copy:
            for pat in {at, at_all, emoji, image, video, voice, audio, file, card}:
                if (res := pat.validate(seg)).success:
                    result.append(res.value)
                    break
            else:
                if seg.is_text():
                    result.append(str(seg))
                else:
                    result.append(Other(seg))
        return result
