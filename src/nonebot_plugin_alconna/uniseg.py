"""通用标注, 无法用于创建 MS对象"""
import re
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

from .typings import gen_unit

Text = str


@dataclass
class Segment:
    """基类标注"""

    origin: MessageSegment


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
class Other(Segment):
    """其他 Segment"""


_Other = gen_unit(
    Other,
    {
        "*": lambda seg: Other(seg),
    },
)


def _handle_kmarkdown_met(seg: MessageSegment):
    content = seg.data["content"]
    if not content.startswith("(met)"):
        return None
    if (end := content.find("(met)", 5)) == -1:
        return None
    return content[5:end] not in ("here", "all") and At(seg, "user", content[5:end])


def _handle_at(seg: MessageSegment):
    if "qq" in seg.data and seg.data["qq"] != "all":
        return At(seg, "user", str(seg.data["qq"]))
    if "user_id" in seg.data:
        return At(seg, "user", str(seg.data["user_id"]))


_At = gen_unit(
    At,
    {
        "at": _handle_at,
        "mention": lambda seg: At(
            seg, "user", seg.data.get("user_id", seg.data.get("text"))
        ),
        "mention_user": lambda seg: At(
            seg, "user", str(seg.data.get("user_id", seg.data["mention_user"].user_id))
        ),
        "mention_channel": lambda seg: At(seg, "channel", str(seg.data["channel_id"])),
        "mention_role": lambda seg: At(seg, "role", str(seg.data["role_id"])),
        "mention_robot": lambda seg: At(
            seg, "user", str(seg.data["mention_robot"].bot_id)
        ),
        "At": lambda seg: At(seg, "user", str(seg, seg.data["target"])),
        "kmarkdown": _handle_kmarkdown_met,
        "room_link": lambda seg: At(
            seg,
            "channel",
            f'{seg.data["room_link"].villa_id}:{seg.data["room_link"].room_id}',
        ),
    },
)
"""
at: ob11, feishu
mention: ob12, tg
mention_user: qqguild, discord, villa
mention_channel: discord, qqguild
mention_role: discord
mention_robot: villa
At: mirai
kmarkdown: kook
room_link: villa
"""


def _handle_kmarkdown_atall(seg: MessageSegment):
    content = seg.data["content"]
    if not content.startswith("(met)"):
        return None
    if (end := content.find("(met)", 5)) == -1:
        return None
    return content[5:end] in ("here", "all") and AtAll(seg)


_AtAll = gen_unit(
    AtAll,
    {
        "at": lambda seg: AtAll(seg) if seg.data["qq"] == "all" else None,
        "AtAll": lambda seg: AtAll(seg),
        "mention_everyone": lambda seg: AtAll(seg),
        "mention_all": lambda seg: AtAll(seg),
        "kmarkdown": _handle_kmarkdown_atall,
    },
)
"""
at: ob11
AtAll: mirai
mention_everyone: discord, qqguild
mention_all: villa, ob12
kmarkdown: kook
"""


def _handle_kmarkdown_emj(seg: MessageSegment):
    content = seg.data["content"]
    if content.startswith("(emj)"):
        mat = re.search(
            r"\(emj\)(?P<name>[^()\[\]]+)\(emj\)\[(?P<id>[^\[\]]+)\]", content
        )
        return mat and Emoji(seg, mat["id"], mat["name"])
    if content.startswith(":"):
        mat = re.search(r":(?P<name>[^:]+):", content)
        return mat and Emoji(seg, mat["name"], mat["name"])


def _handle_custom_emoji(seg: MessageSegment):
    if "custom_emoji_id" in seg.data:  # telegram
        return Emoji(seg, seg.data["custom_emoji_id"], seg.data["text"])
    if "id" in seg.data:  # discord
        return Emoji(seg, seg.data["id"], seg.data["name"])


_Emoji = gen_unit(
    Emoji,
    {
        "emoji": lambda seg: Emoji(seg, str(seg.data.get("id", seg.data.get("name")))),
        "Face": lambda seg: Emoji(seg, str(seg.data["faceId"]), seg.data["name"]),
        "face": lambda seg: str(Emoji(seg, seg.data["id"])),
        "custom_emoji": _handle_custom_emoji,
        "kmarkdown": _handle_kmarkdown_emj,
        "sticker": lambda seg: Emoji(seg, seg.data["id"]) if "id" in seg.data else None,
    },
)


def _handle_image(seg: MessageSegment):
    if "file_id" in seg.data:  # ob12
        return Image(seg, id=seg.data["file_id"])
    if "image" in seg.data:  # villa
        return Image(seg, url=seg.data["image"].url)
    if "image_key" in seg.data:  # feishu
        return Image(seg, url=seg.data["image_key"])
    if "file_key" in seg.data:  # kook
        return Image(seg, url=seg.data["file_key"])
    if "url" in seg.data:  # ob11
        return Image(seg, url=seg.data["url"], id=seg.data["file"])
    if "msgData" in seg.data:  # minecraft
        return Image(seg, url=seg.data["msgData"])
    if "file_path" in seg.data:  # ntchat
        return Image(seg, id=seg.data["file_path"])
    if "picURL" in seg.data:  # ding
        return Image(seg, url=seg.data["picURL"])


def _handle_attachment(seg: MessageSegment):
    if "url" in seg.data:  # qqguild:
        return Image(seg, url=seg.data["url"])
    if "attachment" in seg.data:  # discord
        return Image(seg, id=seg.data["attachment"].filename)


_Image = gen_unit(
    Image,
    {
        "image": _handle_image,
        "photo": lambda seg: Image(seg, id=seg.data["file"]),
        "attachment": _handle_attachment,
        "Image": lambda seg: Image(seg, seg.data["url"], seg.data["imageId"]),
    },
)


def _handle_video(seg: MessageSegment):
    if "file_id" in seg.data:  # ob12, telegram
        return Video(seg, id=seg.data["file_id"])
    if "file" in seg.data:  # ob11
        return Video(seg, url=seg.data["file"])
    if "file_key" in seg.data:  # kook
        return Video(seg, url=seg.data["file_key"])
    if "msgData" in seg.data:  # minecraft
        return Video(seg, url=seg.data["msgData"])
    if "file_path" in seg.data:  # ntchat
        return Video(seg, id=seg.data["file_path"])


_Video = gen_unit(
    Video,
    {
        "video": lambda seg: Video(seg, seg.data["url"], seg.data["videoId"]),
        "animation": lambda seg: Video(seg, id=seg.data["file_id"]),
    },
)


def _handle_voice(seg: MessageSegment):
    if "file_id" in seg.data:  # ob12, telegram
        return Voice(seg, id=seg.data["file_id"])
    if "file_key" in seg.data:  # kook
        return Voice(seg, url=seg.data["file_key"])
    if "file_path" in seg.data:  # ntchat
        return Voice(seg, id=seg.data["file_path"])


_Voice = gen_unit(
    Voice,
    {
        "voice": _handle_voice,
        "record": lambda seg: Voice(seg, seg.data["url"]),
        "Voice": lambda seg: Voice(seg, seg.data["url"], seg.data["voiceId"]),
    },
)


def _handle_audio(seg: MessageSegment):
    if "file_id" in seg.data:  # ob12, telegram
        return Audio(seg, id=seg.data["file_id"])
    if "file_key" in seg.data:  # kook, feishu
        return Audio(seg, url=seg.data["file_key"])
    if "file_path" in seg.data:  # ntchat
        return Audio(seg, id=seg.data["file_path"])


_Audio = gen_unit(
    Audio,
    {
        "audio": _handle_audio,
    },
)


def _handle_file(seg: MessageSegment):
    if "file_id" in seg.data:  # ob12
        return File(seg, id=seg.data["file_id"])
    if "file_key" in seg.data:  # feishu, kook
        return File(
            seg,
            id=seg.data["file_key"],
            name=seg.data.get("file_name", seg.data.get("title")),
        )
    if "file_path" in seg.data:  # ntchat
        return File(seg, id=seg.data["file_path"])


_File = gen_unit(
    File,
    {
        "file": _handle_file,
        "document": lambda seg: File(seg, seg.data["file_id"], seg.data["file_name"]),
        "File": lambda seg: File(seg, seg.data["id"], seg.data["name"]),
    },
)


def _handle_quote(seg: MessageSegment):
    if "msg_id" in seg.data:  # kook:
        return Reply(seg, seg.data["msg_id"], seg.data.get("content"))
    if "quoted_message_id" in seg.data:  # villa
        return Reply(seg, seg.data["quoted_message_id"])


_Reply = gen_unit(
    Reply,
    {
        "reference": lambda seg: Reply(
            seg, seg.data.get("message_id", seg.data["reference"].message_id)
        ),
        "reply": lambda seg: Reply(seg, seg.data.get("id", seg.data["message_id"])),
        "quote": _handle_quote,
        "Quote": lambda seg: Reply(seg, str(seg.data["id"]), str(seg.data["origin"])),
    },
)

env = create_local_patterns("nonebot")
env.sets([_At, _AtAll, _Image, _Video, _Voice, _Audio, _File, _Reply, _Other])
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

    elif reply := getattr(event, "reply", None):
        return Reply(reply, str(reply.message_id), getattr(reply, "message", None))
    return None


class UniMessage(List[US]):
    """通用消息序列

    参数:
        message: 消息内容
    """

    def __str__(self) -> str:
        return "".join(str(seg) for seg in self)

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
        if reply := await reply_handle(event, bot):
            result.append(reply)
        elif (res := _Reply.validate(msg[0])).success:
            result.append(res.value)
            msg_copy.pop(0)
        for seg in msg_copy:
            for pat in {_At, _AtAll, _Image, _Video, _Voice, _Audio, _File}:
                if (res := pat.validate(seg)).success:
                    result.append(res.value)
                    break
            else:
                if seg.is_text():
                    result.append(str(seg))
                else:
                    result.append(Other(seg))
        return result
