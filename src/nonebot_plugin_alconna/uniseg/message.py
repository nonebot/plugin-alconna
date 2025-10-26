from __future__ import annotations

from collections.abc import Iterable, Sequence
from copy import deepcopy
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, Literal, NoReturn, Protocol, TypeVar, Union
from typing_extensions import Self, SupportsIndex, deprecated

from nonebot.exception import FinishedException
from nonebot.internal.adapter import Bot, Event, Message
from nonebot.internal.matcher import current_bot, current_event
from tarina import lang
from tarina.context import ContextModel
from tarina.lang.model import LangItem

from .adapters import alter_get_builder, alter_get_exporter
from .constraint import SerializeFailed
from .fallback import FallbackMessage, FallbackStrategy
from .functions import get_message_id, get_target
from .receipt import Receipt
from .segment import (
    At,
    AtAll,
    Audio,
    Button,
    CustomNode,
    Emoji,
    File,
    Hyper,
    I18n,
    Image,
    Keyboard,
    Reference,
    RefNode,
    Reply,
    Segment,
    Text,
    Video,
    Voice,
    get_segment_class,
)
from .target import Target
from .template import UniMessageTemplate

TS = TypeVar("TS", bound=Segment)
_TM = TypeVar("_TM", bound="str | Message | UniMessage")


class _method:
    def __init__(self, func: FunctionType):
        self.__func__ = func

    def __get__(self, instance, owner):
        if instance is None:
            return self.__func__.__get__(owner, owner)
        return self.__func__.__get__(instance, owner)


class SendWrapper(Protocol):
    async def __call__(self, bot: Bot, event: Event, send: _TM) -> _TM: ...


current_send_wrapper: ContextModel[SendWrapper] = ContextModel("nonebot_plugin_alconna.uniseg.send_wrapper")
MessageContainer = Union[str, Segment, Sequence["MessageContainer"], "UniMessage"]


class UniMessage(list[TS]):
    """通用消息序列

    参数:
        message: 消息内容
    """

    @_method
    def text(cls_or_self: UniMessage | type[UniMessage], text: str):
        """创建纯文本消息

        参数:
            text: 文本内容

        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(Text(text))
            return cls_or_self
        return UniMessage(Text(text))

    @_method
    def style(cls_or_self: UniMessage | type[UniMessage], content: str, *style: str):
        """创建带样式的文本消息

        参数:
            content: 文本内容
            style: 样式

        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(Text(content).mark(None, None, *style))
            return cls_or_self
        return UniMessage(Text(content).mark(None, None, *style))

    @_method
    def at(cls_or_self: UniMessage | type[UniMessage], user_id: str):
        """创建 @用户 消息

        参数:
            user_id: 要 @ 的用户 ID

        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(At("user", user_id))
            return cls_or_self
        return UniMessage(At("user", user_id))

    @_method
    def at_role(cls_or_self: UniMessage | type[UniMessage], role_id: str):
        """创建 @角色组 消息

        参数:
            role_id: 要 @ 的角色 ID

        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(At("role", role_id))
            return cls_or_self
        return UniMessage(At("role", role_id))

    @_method
    def at_channel(cls_or_self: UniMessage | type[UniMessage], channel_id: str):
        """创建 #频道 消息

        参数:
            channel_id: 要 @ 的频道 ID

        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(At("channel", channel_id))
            return cls_or_self
        return UniMessage(At("channel", channel_id))

    @_method
    def at_all(cls_or_self: UniMessage | type[UniMessage], online: bool = False):
        """创建 @全体成员 消息

        参数:
            online: 是否只 @ 在线成员

        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(AtAll(online))
            return cls_or_self
        return UniMessage(AtAll(online))

    @_method
    def emoji(cls_or_self: UniMessage | type[UniMessage], id: str, name: str | None = None):
        """创建 emoji 消息

        参数:
            id: emoji ID
            name: emoji 名称

        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(Emoji(id, name))
            return cls_or_self
        return UniMessage(Emoji(id, name))

    @_method
    def image(
        cls_or_self: UniMessage | type[UniMessage],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        width: int | None = None,
        height: int | None = None,
        sticker: bool = False,
        name: str = "image.png",
    ):
        """创建图片消息

        参数:
            id: 图片 ID
            url: 图片链接
            path: 图片路径
            raw: 图片原始数据
            mimetype: 图片 MIME 类型
            name: 图片名称
            width: 图片宽度
            height: 图片高度
            sticker: 是否为表情贴纸
        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(Image(id, url, path, raw, mimetype, name, width, height, sticker))
            return cls_or_self
        return UniMessage(Image(id, url, path, raw, mimetype, name, width, height, sticker))

    @_method
    def video(
        cls_or_self: UniMessage | type[UniMessage],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        thumbnail: Image | None = None,
        name: str = "video.mp4",
    ):
        """创建视频消息

        参数:
            id: 视频 ID
            url: 视频链接
            path: 视频路径
            raw: 视频原始数据
            mimetype: 视频 MIME 类型
            thumbnail: 视频缩略图
            name: 视频名称
        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(Video(id, url, path, raw, mimetype, name, thumbnail))
            return cls_or_self
        return UniMessage(Video(id, url, path, raw, mimetype, name, thumbnail))

    @_method
    def voice(
        cls_or_self: UniMessage | type[UniMessage],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        duration: float | None = None,
        name: str = "voice.wav",
    ):
        """创建语音消息

        参数:
            id: 语音 ID
            url: 语音链接
            path: 语音路径
            raw: 语音原始数据
            mimetype: 语音 MIME 类型
            duration: 语音时长
            name: 语音名称
        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(Voice(id, url, path, raw, mimetype, name, duration))
            return cls_or_self
        return UniMessage(Voice(id, url, path, raw, mimetype, name, duration))

    @_method
    def audio(
        cls_or_self: UniMessage | type[UniMessage],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        duration: float | None = None,
        name: str = "audio.mp3",
    ):
        """创建音频消息

        参数:
            id: 音频 ID
            url: 音频链接
            path: 音频路径
            raw: 音频原始数据
            mimetype: 音频 MIME 类型
            duration: 音频时长
            name: 音频名称
        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(Audio(id, url, path, raw, mimetype, name, duration))
            return cls_or_self
        return UniMessage(Audio(id, url, path, raw, mimetype, name, duration))

    @_method
    def file(
        cls_or_self: UniMessage | type[UniMessage],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        name: str = "file.bin",
    ):
        """创建文件消息

        参数:
            id: 文件 ID
            url: 文件链接
            path: 文件路径
            raw: 文件原始数据
            mimetype: 文件 MIME 类型
            name: 文件名称
        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(File(id, url, path, raw, mimetype, name))
            return cls_or_self
        return UniMessage(File(id, url, path, raw, mimetype, name))

    @_method
    def reply(cls_or_self: UniMessage | type[UniMessage], id: str):
        """创建回复消息

        参数:
            id: 回复消息 ID

        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(Reply(id))
            return cls_or_self
        return UniMessage(Reply(id))

    @_method
    def hyper(cls_or_self: UniMessage | type[UniMessage], flag: Literal["xml", "json"], content: str):
        """创建卡片消息

        参数:
            flag: 卡片类型
            content: 卡片内容

        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(Hyper(flag, content))
            return cls_or_self
        return UniMessage(Hyper(flag, content))

    @_method
    def reference(cls_or_self: UniMessage | type[UniMessage], *nodes: RefNode | CustomNode, id: str | None = None):
        """创建转发消息

        参数:
            nodes: 转发消息节点
            id: 此处不一定是消息ID，可能是其他ID，如消息序号等

        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(Reference(id=id, nodes=list(nodes)))
            return cls_or_self
        return UniMessage(Reference(id=id, nodes=list(nodes)))

    @_method
    def keyboard(
        cls_or_self: UniMessage | type[UniMessage],
        *buttons: Button,
        id: str | None = None,
        row: int | None = None,
    ):
        """创建转发消息

        参数:
            buttons: 按钮
            id: 此处一般用来表示模板id，特殊情况下可能表示例如 bot_appid 等
            row: 当消息中只写有一个 Keyboard 时可根据此参数约定按钮组的列数

        返回:
            构建的消息
        """
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(Keyboard(id=id, buttons=list(buttons), row=row))
            return cls_or_self
        return UniMessage(Keyboard(id=id, buttons=list(buttons), row=row))

    @_method
    def i18n(
        cls_or_self: UniMessage | type[UniMessage],
        item_or_scope: LangItem | str,
        type_: str | None = None,
        /,
        *args,
        mapping: dict | None = None,
        **kwargs,
    ):
        """创建 i18n 消息"""
        if isinstance(cls_or_self, UniMessage):
            cls_or_self.append(I18n(item_or_scope, type_, *args, mapping=mapping, **kwargs))  # type: ignore
            return cls_or_self
        return UniMessage(I18n(item_or_scope, type_, *args, mapping=mapping, **kwargs))  # type: ignore

    def __init__(
        self: UniMessage,
        message: Iterable[str | Segment] | str | Segment | None = None,
    ):
        super().__init__()
        if isinstance(message, str):
            self.__iadd__(Text(message), _merge=False)
        elif isinstance(message, Iterable):
            for i in message:
                self.__iadd__(Text(i) if isinstance(i, str) else i, _merge=False)
        elif isinstance(message, Segment):
            self.__iadd__(message, _merge=False)
        self.__merge_text__()

    def __str__(self) -> str:
        return "".join(str(seg) for seg in self)

    def __repr__(self) -> str:
        return "[" + ", ".join(repr(seg) for seg in self) + "]"

    def __format__(self, format_spec):
        if format_spec in ("#", "*"):
            return "".join(format(seg, format_spec) for seg in self)
        return format(self.__str__(), format_spec)

    @classmethod
    def template(cls, format_string: str | UniMessage) -> UniMessageTemplate:
        """创建消息模板。

        用法和 `str.format` 大致相同，支持以 `UniMessage` 对象作为消息模板并输出消息对象。
        并且提供了拓展的格式化控制符，可以通过 `Segment` 的实例化方法创建消息。

        参数:
            format_string: 格式化模板

        返回:
            消息格式化器
        """
        return UniMessageTemplate(format_string, cls)  # type: ignore

    def __merge_text__(self) -> Self:
        if not self:
            return self
        result = []
        last = list.__getitem__(self, 0)
        for seg in list.__getitem__(self, slice(1, None)):
            if isinstance(seg, Text) and isinstance(last, Text):
                last += seg
            else:
                result.append(last)
                last = seg
        result.append(last)
        self.clear()
        self.extend(result)
        return self

    def __add__(self, other: str | TS | Segment | Iterable[TS | Segment]) -> UniMessage:
        result: UniMessage = self.copy()
        if isinstance(other, str):
            if result and isinstance(text := result[-1], Text):
                text.text += other
            else:
                result.append(Text(other))
        elif isinstance(other, Segment):
            result.append(other)
        elif isinstance(other, Iterable):
            for seg in other:
                result += seg
        else:
            raise TypeError(f"Unsupported type {type(other)!r}")
        result.__merge_text__()
        return result

    def __radd__(self, other: str | Segment | Iterable[Segment]) -> UniMessage:
        result = UniMessage(other)
        return result + self

    def __iadd__(self, other: str | TS | Iterable[TS], _merge: bool = True):
        if isinstance(other, str):
            if self and isinstance(text := self[-1], Text):
                text.text += other
            else:
                self.append(Text(other))  # type: ignore
        elif isinstance(other, Segment):
            self.append(other)
        elif isinstance(other, Iterable):
            for seg in other:
                self.__iadd__(seg, _merge)
        else:
            raise TypeError(f"Unsupported type {type(other)!r}")
        if _merge:
            self.__merge_text__()
        return self

    def __getitem__(
        self,
        args: type[Segment] | tuple[type[Segment], int] | tuple[type[Segment], slice] | int | slice,
    ):
        arg1, arg2 = args if isinstance(args, tuple) else (args, None)
        if isinstance(arg1, int) and arg2 is None:
            return list.__getitem__(self, arg1)
        if isinstance(arg1, slice) and arg2 is None:
            return UniMessage(list.__getitem__(self, arg1))
        if TYPE_CHECKING:
            assert not isinstance(arg1, (slice, int))
        if issubclass(arg1, Segment) and arg2 is None:
            return UniMessage(seg for seg in self if isinstance(seg, arg1))
        if issubclass(arg1, Segment) and isinstance(arg2, int):
            return [seg for seg in self if isinstance(seg, arg1)][arg2]
        if issubclass(arg1, Segment) and isinstance(arg2, slice):
            return UniMessage([seg for seg in self if isinstance(seg, arg1)][arg2])
        raise ValueError("Incorrect arguments to slice")  # pragma: no cover

    def __contains__(self, value: str | Segment | type[Segment]) -> bool:
        """检查消息段是否存在

        参数:
            value: 消息段或消息段类型
        返回:
            消息内是否存在给定消息段或给定类型的消息段
        """
        if isinstance(value, type):
            return bool(next((seg for seg in self if isinstance(seg, value)), None))
        if isinstance(value, str):
            value = Text(value)
        return super().__contains__(value)

    def has(self, value: str | Segment | type[Segment]) -> bool:
        """与 {ref}``__contains__` <nonebot.adapters.Message.__contains__>` 相同"""
        return value in self

    def index(self, value: str | Segment | type[Segment], *args: SupportsIndex) -> int:
        """索引消息段

        参数:
            value: 消息段或者消息段类型
            arg: start 与 end

        返回:
            索引 index

        异常:
            ValueError: 消息段不存在
        """
        if isinstance(value, type):
            first_segment = next((seg for seg in self if isinstance(seg, value)), None)
            if first_segment is None:
                raise ValueError(f"Segment with type {value!r} is not in message")
            return super().index(first_segment, *args)
        if isinstance(value, str):
            value = Text(value)
        return super().index(value, *args)  # type: ignore

    def get(self, type_: type[TS], count: int | None = None) -> UniMessage:
        """获取指定类型的消息段

        参数:
            type_: 消息段类型
            count: 获取个数

        返回:
            构建的新消息
        """
        if count is None:
            return self[type_]  # type: ignore

        iterator, filtered = (seg for seg in self if isinstance(seg, type_)), UniMessage()
        for _ in range(count):
            seg = next(iterator, None)
            if seg is None:
                break
            filtered.append(seg)
        return filtered  # type: ignore

    def count(self, value: type[Segment] | str | Segment) -> int:
        """计算指定消息段的个数

        参数:
            value: 消息段或消息段类型

        返回:
            个数
        """
        if isinstance(value, str):
            value = Text(value)
        return (
            len(self[value])  # type: ignore
            if isinstance(value, type)
            else super().count(value)  # type: ignore
        )

    def only(self, value: type[Segment] | str | Segment) -> bool:
        """检查消息中是否仅包含指定消息段

        参数:
            value: 指定消息段或消息段类型

        返回:
            是否仅包含指定消息段
        """
        if isinstance(value, type):
            return all(isinstance(seg, value) for seg in self)
        if isinstance(value, str):
            value = Text(value)
        return all(seg == value for seg in self)

    def join(self, iterable: Iterable[Segment | UniMessage[Segment]]):
        """将多个消息连接并将自身作为分割

        参数:
            iterable: 要连接的消息

        返回:
            连接后的消息
        """
        ret = UniMessage()
        for index, msg in enumerate(iterable):
            if index != 0:
                ret.extend(self)
            if isinstance(msg, Segment):
                ret.append(msg)
            else:
                ret.extend(msg.copy())
        return ret  # type: ignore

    def copy(self) -> UniMessage[TS]:
        """深拷贝消息"""
        return deepcopy(self)

    def include(self, *types: type[Segment]):
        """过滤消息

        参数:
            types: 包含的消息段类型

        返回:
            新构造的消息
        """
        return self.__class__(seg for seg in self if seg.__class__ in types)

    def exclude(self, *types: type[Segment]):
        """过滤消息

        参数:
            types: 不包含的消息段类型

        返回:
            新构造的消息
        """
        return UniMessage(seg for seg in self if seg.__class__ not in types)

    def extract_plain_text(self) -> str:
        """提取消息内纯文本消息"""

        return "".join(seg.text for seg in self if isinstance(seg, Text))

    def filter(self, predicate: Callable[[TS], bool]):
        """过滤消息

        参数:
            target: 消息段类型
            predicate: 过滤函数
        """
        return UniMessage(seg for seg in self if predicate(seg))

    def map(self, func: Callable[[TS], Segment] | Callable[[TS], Any]):
        result1 = []
        result2 = []
        for seg in self:
            result = func(seg)
            if isinstance(result, Segment):
                result1.append(result)
            else:
                result2.append(result)
        if result1:
            return UniMessage(result1)
        return result2

    def select(self, cls: type[Segment]):
        """递归地从消息中选择指定类型的消息段"""

        def query(segs: list[Segment]):
            for s in segs:
                if isinstance(s, cls):
                    yield s
                yield from query(s.children)

        results = []
        for seg in self:
            if isinstance(seg, cls):
                results.append(seg)
            results.extend(query(seg.children))
        return UniMessage(results)

    @staticmethod
    def _visit_sync(seg: Segment, rules: dict | Callable[[Segment], Any]):
        _type, data, children = seg.type, seg.data, seg.children
        if not isinstance(rules, dict):
            return rules(seg)
        result = rules.get(_type, True)
        if not isinstance(result, (bool, Segment, Iterable)):
            result = result(data, children)
        return result

    @staticmethod
    async def _visit_async(seg: Segment, rules: dict | Callable[[Segment], Any]):
        _type, data, children = seg.type, seg.data, seg.children
        if not isinstance(rules, dict):
            return await rules(seg)
        result = rules.get(_type, True)
        if not isinstance(result, (bool, Segment, Iterable)):
            result = await result(data, children)
        return result

    def transform(self, rules: dict) -> UniMessage:
        """同步遍历消息段并转换

        参数:
            rules: 转换规则

        返回:
            转换后的消息
        """
        output = UniMessage()
        for seg in self:
            result = self._visit_sync(seg, rules)
            if result is True:
                output.append(seg)
            elif result is not False:
                if isinstance(result, Segment):
                    output.append(result)
                else:
                    output.extend(result)
        output.__merge_text__()
        return output

    async def transform_async(self, rules: dict) -> UniMessage:
        """异步遍历消息段并转换

        参数:
            rules: 转换规则

        返回:
            转换后的消息
        """
        output = UniMessage()
        for seg in self:
            result = await self._visit_async(seg, rules)
            if result is True:
                output.append(seg)
            elif result is not False:
                if isinstance(result, Segment):
                    output.append(result)
                else:
                    output.extend(result)
        output.__merge_text__()
        return output

    def split(self, pattern: str = " ") -> list[UniMessage]:
        """和 `str.split` 差不多, 提供一个字符串, 然后返回分割结果.

        Args:
            pattern (str): 分隔符. 默认为单个空格.

        Returns:
            list[Self]: 分割结果, 行为和 `str.split` 差不多.
        """

        result: list[UniMessage] = []
        tmp = []
        for seg in self:
            if isinstance(seg, Text):
                split_result = seg.split(pattern)
                for index, split_text in enumerate(split_result):
                    if tmp and index > 0:
                        result.append(UniMessage(tmp))
                        tmp = []
                    if split_text.text:
                        tmp.append(split_text)
            else:
                tmp.append(seg)
        if tmp:
            result.append(UniMessage(tmp))
            tmp = []
        return result

    def replace(self, old: str, new: str | Text):
        """替换消息中有关的文本

        Args:
            old (str): 要替换的字符串.
            new (str | Text): 替换后的字符串/文本元素.

        Returns:
            UniMessage: 修改后的消息链, 若未替换则原样返回.
        """
        result_list = []
        for seg in self:
            if isinstance(seg, Text):
                result_list.append(seg.replace(old, new))  # type: ignore
            else:
                result_list.append(seg)
        return UniMessage(result_list)

    def startswith(self, string: str) -> bool:
        """判断消息链是否以给出的字符串开头

        Args:
            string (str): 字符串

        Returns:
            bool: 是否以给出的字符串开头
        """

        if not self or not isinstance(self[0], Text):
            return False
        return list.__getitem__(self, 0).text.startswith(string)

    def endswith(self, string: str) -> bool:
        """判断消息链是否以给出的字符串结尾

        Args:
            string (str): 字符串

        Returns:
            bool: 是否以给出的字符串结尾
        """

        if not self or not isinstance(self[-1], Text):
            return False
        return list.__getitem__(self, -1).text.endswith(string)

    def removeprefix(self, prefix: str):
        """移除消息链前缀.

        Args:
            prefix (str): 要移除的前缀.

        Returns:
            UniMessage: 修改后的消息链.
        """
        copy = list.copy(self)
        if not copy:
            return UniMessage(copy)
        seg = copy[0]
        if not isinstance(seg, Text):
            return UniMessage(copy)
        if seg.text.startswith(prefix):
            seg = seg[len(prefix) :]
            if not seg.text:
                copy.pop(0)
            else:
                copy[0] = seg
        return UniMessage(copy)

    def removesuffix(self, suffix: str):
        """移除消息链后缀.

        Args:
            suffix (str): 要移除的后缀.

        Returns:
            UniMessage: 修改后的消息链.
        """
        copy = list.copy(self)
        if not copy:
            return UniMessage(copy)
        seg = copy[-1]
        if not isinstance(seg, Text):
            return UniMessage(copy)
        if seg.text.endswith(suffix):
            seg = seg[: -len(suffix)]
            if not seg.text:
                copy.pop(-1)
            else:
                copy[-1] = seg
        return UniMessage(copy)

    def strip(self, *segments: str | Segment | type[Segment]):
        return self.lstrip(*segments).rstrip(*segments)

    def lstrip(self, *segments: str | Segment | type[Segment]):
        types = [i for i in segments if not isinstance(i, str)] or []
        chars = "".join([i for i in segments if isinstance(i, str)]) or None
        copy = list.copy(self)
        if not copy:
            return self.__class__(copy)
        while copy:
            seg = copy[0]
            if seg in types or seg.__class__ in types:
                copy.pop(0)
            elif isinstance(seg, Text):
                seg = seg.lstrip(chars)
                if not seg.text:
                    copy.pop(0)
                    continue
                copy[0] = seg
                break
            else:
                break
        return self.__class__(copy)

    def rstrip(self, *segments: str | Segment | type[Segment]):
        types = [i for i in segments if not isinstance(i, str)] or []
        chars = "".join([i for i in segments if isinstance(i, str)]) or None
        copy = list.copy(self)
        if not copy:
            return self.__class__(copy)
        while copy:
            seg = copy[-1]
            if seg in types or seg.__class__ in types:
                copy.pop(-1)
            elif isinstance(seg, Text):
                seg = seg.rstrip(chars)
                if not seg.text:
                    copy.pop(-1)
                    continue
                copy[-1] = seg
                break
            else:
                break
        return self.__class__(copy)

    @staticmethod
    @deprecated("`UniMessage.generate` is deprecated, use `UniMessage.of()` and `await msg.attach_reply()` instead")
    async def generate(
        *,
        message: Message | None = None,
        event: Event | None = None,
        bot: Bot | None = None,
        adapter: str | None = None,
    ) -> UniMessage:
        if message is None:
            if not event:
                try:
                    event = current_event.get()
                except LookupError as e:
                    raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
            try:
                message = event.get_message()
            except Exception:
                return UniMessage()
        return await UniMessage.of(message, bot=bot, adapter=adapter).attach_reply(event, bot)

    @staticmethod
    @deprecated("`UniMessage.generate_sync` is deprecated, use `UniMessage.of` instead")
    def generate_sync(
        *,
        message: Message | None = None,
        event: Event | None = None,
        bot: Bot | None = None,
        adapter: str | None = None,
    ) -> UniMessage:
        if message is None:
            if not event:
                try:
                    event = current_event.get()
                except LookupError as e:
                    raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
            try:
                message = event.get_message()
            except Exception:
                return UniMessage()
        return UniMessage.of(message, bot=bot, adapter=adapter)

    generate_without_reply = generate_sync

    @classmethod
    def of(
        cls,
        message: Message,
        bot: Bot | None = None,
        adapter: str | None = None,
    ):
        if not adapter:
            if not bot:
                try:
                    bot = current_bot.get()
                except LookupError as e:
                    raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
            _adapter = bot.adapter
            adapter = _adapter.get_name()
        if not (fn := alter_get_builder(adapter)):
            raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))
        return UniMessage(fn.generate(message))

    async def attach_reply(self, event: Event | None = None, bot: Bot | None = None) -> Self:
        if not event:
            try:
                event = current_event.get()
            except LookupError as e:
                raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
        if not bot:
            try:
                bot = current_bot.get()
            except LookupError as e:
                raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
        if not (fn := alter_get_builder(bot.adapter.get_name())):
            raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=bot.adapter.get_name()))
        if _reply := await fn.extract_reply(event, bot):
            if self.has(Reply) and self.index(Reply) == 0:
                self.pop(0)
            self.insert(0, _reply)  # type: ignore
        return self

    def _handle_i18n(self, extra: dict, *args, **kwargs):
        segments = [*self]
        self.clear()
        for seg in segments:
            if not isinstance(seg, I18n):
                self.append(seg)
            else:
                msg = self.template(str(seg)).format(*args, *seg.args, **kwargs, **seg.kwargs, **extra)
                if msg.has(I18n):
                    msg._handle_i18n(extra, *seg.args, **seg.kwargs)  # type: ignore
                self.extend(msg)
        self.__merge_text__()

    async def export(
        self,
        bot: Bot | None = None,
        fallback: bool | FallbackStrategy = FallbackStrategy.auto,
        adapter: str | None = None,
    ) -> Message:
        """将 UniMessage 转换为指定适配器下的 Message"""
        if not adapter:
            if not bot:
                try:
                    bot = current_bot.get()
                except LookupError as e:
                    raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
            adapter = bot.adapter.get_name()
        if self.has(I18n):
            extra = {}
            try:
                event = current_event.get()
                extra["$event"] = event
                extra["$target"] = get_target(event, bot, adapter)
                msg_id = get_message_id(event, bot, adapter)
                extra["$message_id"] = msg_id
            except (LookupError, NotImplementedError, SerializeFailed):
                pass
            self._handle_i18n(extra)
        try:
            if fn := alter_get_exporter(adapter):
                return await fn.export(self, bot, fallback)
            raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))
        except SerializeFailed:
            if fallback and fallback != FallbackStrategy.forbid:
                return FallbackMessage(str(self))
            raise

    def export_sync(
        self,
        fallback: bool | FallbackStrategy = FallbackStrategy.auto,
        adapter: str | None = None,
    ) -> Message:
        """（实验性）同步方法地将 UniMessage 转换为指定适配器下的 Message"""
        coro = self.export(None, fallback, adapter)
        try:
            return coro.send(None)
        except StopIteration as e:
            return e.args[0]

    async def send(
        self,
        target: Event | Target | None = None,
        bot: Bot | None = None,
        fallback: bool | FallbackStrategy = FallbackStrategy.auto,
        at_sender: str | bool = False,
        reply_to: str | bool | Reply | None = False,
        no_wrapper: bool = False,
        **kwargs,
    ) -> Receipt:
        if not target:
            try:
                target = current_event.get()
            except LookupError as e:
                raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
        if not bot:
            if isinstance(target, Target):
                try:
                    bot = await target.select()
                except Exception as e:
                    raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
            else:
                try:
                    bot = current_bot.get()
                except LookupError as e:
                    raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
        if at_sender:
            _target = target if isinstance(target, Target) else get_target(target, bot)
            if not _target.private:
                if isinstance(at_sender, str):
                    self.insert(0, At("user", at_sender))  # type: ignore
                elif isinstance(target, Event):
                    self.insert(0, At("user", target.get_user_id()))  # type: ignore
                else:
                    raise TypeError("at_sender must be str when target is not Event")
        if reply_to:
            if isinstance(reply_to, Reply):
                self.insert(0, reply_to)  # type: ignore
            else:
                if isinstance(reply_to, bool):
                    if isinstance(target, Event):
                        reply_to = get_message_id(target, bot)
                    else:
                        raise TypeError("reply_to must be str when target is not Event")
                self.insert(0, Reply(reply_to))  # type: ignore
        if not no_wrapper and isinstance(target, Event) and (wrapper := current_send_wrapper.get(None)):
            self[:] = await wrapper(bot, target, self)
        msg = await self.export(bot, fallback)
        adapter = bot.adapter
        adapter_name = adapter.get_name()
        if not (fn := alter_get_exporter(adapter_name)):
            raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter_name))
        res = await fn.send_to(target, bot, msg, **kwargs)
        return Receipt(bot, target, fn, res if isinstance(res, list) else [res], UniMessage)  # type: ignore

    async def finish(
        self,
        target: Event | Target | None = None,
        bot: Bot | None = None,
        fallback: bool | FallbackStrategy = FallbackStrategy.auto,
        at_sender: str | bool = False,
        reply_to: str | bool | Reply | None = False,
        **kwargs,
    ) -> NoReturn:
        await self.send(target, bot, fallback, at_sender, reply_to, **kwargs)
        raise FinishedException

    def dump(self, media_save_dir: str | Path | bool | None = None, json: bool = False) -> str | list[dict[str, Any]]:
        """将消息序列化为 JSON 格式

        注意：
            若 media_save_dir 为 False，则不会保存媒体文件。
            若 media_save_dir 为 True，则会将文件数据转为 base64 编码。
            若不指定 media_save_dir，则会尝试导入 `nonebot_plugin_localstore` 并使用其提供的路径。
            否则，将会尝试使用当前工作目录。

        Args:
            media_save_dir (Union[str, Path， bool, None], optional): 媒体文件保存路径. Defaults to None.
            json (bool, optional): 是否返回 JSON 字符串. Defaults to False.

        Returns:
            Union[str, list[dict]]: 序列化后的消息
        """
        result = [seg.dump(media_save_dir=media_save_dir) for seg in self]
        return dumps(result, ensure_ascii=False) if json else result

    @classmethod
    def load(cls: type[UniMessage[Segment]], data: str | list[dict[str, Any]]):
        """从 JSON 数据加载消息

        Args:
            data (Union[str, list[dict[str, Any]]]): JSON 数据

        Returns:
            UniMessage: 加载后的消息
        """
        if isinstance(data, str):
            _data: list[dict[str, Any]] = loads(data)
        else:
            _data = data
        return cls(get_segment_class(seg_data["type"]).load(seg_data) for seg_data in _data)
