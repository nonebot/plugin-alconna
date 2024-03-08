from __future__ import annotations

from typing_extensions import Self, ParamSpec, TypeAlias
from typing import Any, Union, Generic, TypeVar, Callable, Awaitable

from tarina import lang
from arclet.alconna import Arparma
from nonebot.typing import T_State
from nonebot.internal.adapter import Bot, Event, Message, MessageSegment
from nepattern import URL, INTEGER, MatchMode, BasePattern, MatchFailed, UnionPattern

from .argv import argv_ctx
from .uniseg.segment import env
from .uniseg import At, Text, Image, Segment, UniMessage

T = TypeVar("T")
TS = TypeVar("TS", bound=Segment)
TMS = TypeVar("TMS", bound=MessageSegment)
TCallable = TypeVar("TCallable", bound=Callable[..., Any])
P = ParamSpec("P")


class _Text(BasePattern[Text, str]):
    def __init__(self):
        super().__init__(
            mode=MatchMode.TYPE_CONVERT,
            origin=Text,
            alias="text",
            accepts=str,
        )

    def spliter(self, x: str):
        current_argv = argv_ctx.get()
        styles = current_argv.context["__styles__"]
        start = styles["msg"].find(x, styles["index"])
        if start == -1:
            return Text(x)
        styles["index"] = start + len(x)
        if maybe := styles["record"].get((start, styles["index"])):
            return Text(x, {(0, len(x)): maybe})
        _styles = {}
        _len = len(x)
        for scale, style in styles["record"].items():
            if start <= scale[0] < styles["index"] <= scale[1]:
                _styles[(scale[0] - start, scale[1] - start)] = style
            elif scale[0] <= start < scale[1] <= styles["index"]:
                _styles[(0, scale[1] - start)] = style
            elif start <= scale[0] < scale[1] <= styles["index"]:
                _styles[(scale[0] - start, scale[1] - start)] = style
            elif scale[0] <= start < styles["index"] <= scale[1]:
                _styles[(scale[0] - start, _len)] = style
        return Text(x, _styles)

    def match(self, input_: str | Text) -> Text:
        if not isinstance(input_, (str, self.origin)):
            raise MatchFailed(lang.require("nepattern", "type_error").format(target=type(input_)))
        if isinstance(input_, str):
            return self.spliter(input_)
        return input_


text = _Text()
env[Text] = text

ImageOrUrl = (
    UnionPattern[Union[str, Image]](
        [
            BasePattern(
                mode=MatchMode.TYPE_CONVERT,
                origin=str,
                converter=lambda _, x: x.url,  # type: ignore
                alias="img",
                accepts=Image,
            ),
            URL,  # type: ignore
        ]
    )
    @ "img_url"
)
"""
内置类型, 允许传入图片元素(Image)或者链接(URL)，返回链接
"""

AtID = (
    UnionPattern[Union[str, At]](
        [
            BasePattern(
                mode=MatchMode.TYPE_CONVERT,
                origin=int,
                alias="At",
                accepts=At,
                converter=lambda _, x: int(x.target),  # type: ignore
            ),
            BasePattern(
                r"@(\d+)",
                mode=MatchMode.REGEX_CONVERT,
                origin=int,
                alias="@xxx",
                accepts=str,
                converter=lambda _, x: int(x[1]),  # type: ignore
            ),
            INTEGER,
        ]
    )
    @ "notice_id"
)
"""
内置类型，允许传入@元素(At)或者'@xxxx'式样的字符串或者数字, 返回数字
"""


class SegmentPattern(BasePattern[TMS, TS], Generic[TS, TMS, P]):
    def __init__(
        self,
        name: str,
        origin: type[TMS],
        accept: type[TS],
        call: Callable[P, TMS],
        additional: Callable[[TS], bool] | None = None,
        handle: Callable[[TS], TMS] | None = None,
    ):
        super().__init__(
            mode=MatchMode.TYPE_CONVERT,
            origin=origin,
            alias=name,
            accepts=accept,
        )
        self.target = accept
        self.pattern = name
        self.call = call
        self.validator: Callable[[TS], bool] = (
            lambda s: isinstance(s.origin, origin) and s.origin.type == name and (additional or (lambda _: True))(s)
        )
        self.handle = handle or (lambda s: s.origin)

    def match(self, input_: Segment) -> TMS:
        if not isinstance(input_, self.target):
            raise MatchFailed(lang.require("nepattern", "type_error").format(target=type(input_)))
        if self.validator(input_):
            return self.handle(input_)  # type: ignore
        raise MatchFailed(lang.require("nepattern", "content_error").format(target=input_))

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> TMS:
        return self.call(*args, **kwargs)  # type: ignore


class TextSegmentPattern(BasePattern[TMS, Union[str, Text]], Generic[TMS, P]):
    def __init__(
        self,
        name: str,
        origin: type[TMS],
        call: Callable[P, TMS],
        converter: Callable[[Any, Text], TMS | None],
    ):
        super().__init__(
            mode=MatchMode.TYPE_CONVERT,
            origin=origin,
            alias=name,
            converter=converter,
            accepts=Text,
            previous=text,
        )
        self.pattern = name
        self.call = call

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> TMS:
        return self.call(*args, **kwargs)  # type: ignore


class Style(BasePattern[Text, Union[str, Text]], Generic[TMS, P]):
    def __init__(
        self,
        expect: str,
    ):
        self.expected = [expect]
        super().__init__(
            mode=MatchMode.VALUE_OPERATE,
            origin=Text,
            converter=lambda _, x: x if all(set(style).issuperset(_.expected) for style in x.styles.values()) else None,  # type: ignore
            alias=expect,
            previous=text,
        )
        self.pattern = expect

    def __call__(self, text: str):
        return Text(text).mark(0, len(text), *self.expected)

    def __add__(self, other: Style) -> Self:
        if not isinstance(other, Style):
            raise TypeError(other)
        if other.pattern not in self.expected:
            self.expected.append(other.pattern)
        self.alias = "+".join(self.expected)
        self.refresh()
        return self


Bold = Style("bold")
Italic = Style("italic")
Underline = Style("underline")
Strikethrough = Style("strikethrough")
Spoiler = Style("spoiler")
Code = Style("code")

MReturn: TypeAlias = Union[
    Union[str, Segment, UniMessage, Message, MessageSegment],
    Awaitable[Union[str, Segment, UniMessage, Message, MessageSegment]],
]
MIDDLEWARE: TypeAlias = Callable[[Event, Bot, T_State, Any], Any]
CHECK: TypeAlias = Callable[[Event, Bot, T_State, Arparma], Awaitable[bool]]
