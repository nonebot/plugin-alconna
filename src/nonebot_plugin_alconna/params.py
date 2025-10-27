from contextlib import AsyncExitStack
import inspect
from typing import Annotated, Any, ClassVar, Literal, Optional, TypeVar, Union, overload
from typing_extensions import Self, get_args, override

from arclet.alconna import Alconna, Arparma, Duplication, Empty
from arclet.alconna.builtin import generate_duplication
from nepattern.util import CUnionType
from nonebot.compat import PydanticUndefined
from nonebot.dependencies import Param
from nonebot.internal.adapter import Bot, Event
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import DependencyCache, Depends
from nonebot.typing import T_State, _DependentCallable
from nonebot.utils import generic_check_issubclass
from tarina import run_always_await
from tarina.generic import get_origin, is_optional

from .consts import ALCONNA_ARG_KEY, ALCONNA_ARG_KEYS, ALCONNA_EXEC_RESULT, ALCONNA_EXTENSION, ALCONNA_RESULT
from .extension import Extension, ExtensionExecutor, SelectedExtensions
from .model import CommandResult, Match, Query, T
from .typings import CHECK, MIDDLEWARE

T_Duplication = TypeVar("T_Duplication", bound=Duplication)
T_Extension = TypeVar("T_Extension", bound=Extension)

_Contents = (Union, CUnionType, Literal)


def _alconna_result(state: T_State) -> CommandResult:
    return state[ALCONNA_RESULT]


def AlconnaResult() -> CommandResult:
    return Depends(_alconna_result, use_cache=False)


def _alconna_exec_result(state: T_State) -> dict[str, Any]:
    return state[ALCONNA_EXEC_RESULT]


def AlconnaExecResult() -> dict[str, Any]:
    return Depends(_alconna_exec_result, use_cache=False)


def _alconna_matches(state: T_State) -> Arparma:
    return _alconna_result(state).result


def AlconnaMatches() -> Arparma:
    return Depends(_alconna_matches, use_cache=False)


def _alconna_ctx(state: T_State):
    return state[ALCONNA_RESULT].context


def AlconnaContext() -> dict[str, Any]:
    return Depends(_alconna_ctx, use_cache=False)


def AlconnaMatch(name: str, middleware: Optional[MIDDLEWARE] = None) -> Match:
    async def _alconna_match(state: T_State, bot: Bot, event: Event) -> Match:
        arp = _alconna_result(state).result
        mat = Match(arp.all_matched_args.get(name, Empty), name in arp.all_matched_args)
        if middleware and mat.available:
            mat.result = await run_always_await(middleware, event, bot, state, mat.result)
        return mat

    return Depends(_alconna_match, use_cache=False)


def merge_path(path: str, parent: str) -> str:
    if not path.startswith("~"):
        return path
    if path.startswith("~."):
        path = path.replace("~.", "~", 1)
    return f"{parent}.{path[1:]}" if parent else path[1:]


def AlconnaQuery(
    path: str,
    default: Union[T, Empty] = Empty,
    middleware: Optional[MIDDLEWARE] = None,
) -> Query[T]:
    async def _alconna_query(state: T_State, bot: Bot, event: Event, matcher: Matcher) -> Query:
        arp = _alconna_result(state).result
        _path = merge_path(path, getattr(matcher, "basepath", ""))
        q = Query(_path, default)
        result = arp.query(_path, Empty)
        q.available = result != Empty
        if q.available:
            q.result = result  # type: ignore
        elif default != Empty:
            q.available = True
        if middleware and q.available:
            q.result = await run_always_await(middleware, event, bot, state, q.result)
        return q

    return Depends(_alconna_query, use_cache=False)


@overload
def AlconnaDuplication() -> Duplication: ...


@overload
def AlconnaDuplication(_t: type[T_Duplication]) -> T_Duplication: ...


def AlconnaDuplication(_t: Optional[type[T_Duplication]] = None) -> Duplication:
    def _alconna_match(state: T_State) -> Duplication:
        res = _alconna_result(state)
        gt = _t or generate_duplication(res.source)
        return gt(res.result)

    return Depends(_alconna_match, use_cache=False)


def AlconnaArg(path: str) -> Any:
    def _alconna_arg(state: T_State) -> Any:
        return state[ALCONNA_ARG_KEY.format(key=path)]

    return Depends(_alconna_arg, use_cache=False)


AlcResult = Annotated[CommandResult, AlconnaResult()]
AlcExecResult = Annotated[dict[str, Any], AlconnaExecResult()]
AlcMatches = Annotated[Arparma, AlconnaMatches()]
AlcContext = Annotated[dict[str, Any], AlconnaContext()]


def match_path(
    path: str,
    additional: Optional[CHECK] = None,
):
    """
    当 Arpamar 解析成功后, 依据 path 是否存在以继续执行事件处理

    当 path 为 ‘$main’ 时表示认定当且仅当主命令匹配
    """

    async def wrapper(event: Event, bot: Bot, state: T_State, result: Arparma):
        if path == "$main":
            return not result.components and (not additional or await additional(event, bot, state, result))
        return result.query(path, "\0") != "\0" and (not additional or await additional(event, bot, state, result))

    return wrapper


def match_value(
    path: str,
    value: Any,
    or_not: bool = False,
    additional: Optional[CHECK] = None,
):
    """
    当 Arpamar 解析成功后, 依据查询 path 得到的结果是否符合传入的值以继续执行事件处理

    当 or_not 为真时允许查询 path 失败时继续执行事件处理
    """

    async def wrapper(event: Event, bot: Bot, state: T_State, result: Arparma):
        if result.query(path, "\0") == value:
            return True and (not additional or await additional(event, bot, state, result))
        return (
            or_not
            and result.query(path, "\0") == "\0"
            and (not additional or await additional(event, bot, state, result))
        )

    return wrapper


_seminal = type("_seminal", (object,), {})


def assign(
    path: str,
    value: Any = _seminal,
    or_not: bool = False,
    additional: Optional[CHECK] = None,
) -> CHECK:
    if value != _seminal:
        return match_value(path, value, or_not, additional)
    if or_not:

        async def wrapper(event: Event, bot: Bot, state: T_State, result: Arparma):
            return await match_path("$main", additional)(event, bot, state, result) or await match_path(
                path, additional
            )(event, bot, state, result)

        return wrapper
    return match_path(path, additional)


def Check(fn: CHECK) -> bool:
    async def _arparma_check(bot: Bot, state: T_State, event: Event, matcher: Matcher) -> bool:
        arp = _alconna_result(state).result
        if not (ans := await fn(event, bot, state, arp)):
            matcher.skip()
        return ans

    return Depends(_arparma_check, use_cache=False)


def AlconnaExtension(target: type[T_Extension]) -> T_Extension:
    def _alconna_extension(state: T_State):
        selected: SelectedExtensions = state[ALCONNA_EXTENSION]
        return next((i for i in selected.context if isinstance(i, target)), None)

    return Depends(_alconna_extension, use_cache=False)


class ExtensionParam(Param):
    """Extension 自定义注入参数"""

    executor: ClassVar[ExtensionExecutor]

    def __repr__(self) -> str:
        return f"ExtensionParam(name={self.extra['name']}, type={self.extra['type']!r})"

    @classmethod
    def new(cls, executor: ExtensionExecutor):
        return type(
            f"ExtensionParam_{executor._rule._path}",
            (cls,),
            {"executor": executor},
        )

    @classmethod
    def _check_param(cls, param: inspect.Parameter, allow_types: tuple[type[Param], ...]) -> Optional["ExtensionParam"]:
        if cls.executor.before_catch(param.name, param.annotation, param.default):
            return cls(param.default, name=param.name, type=param.annotation, validate=True)
        return None

    async def _solve(self, event: Event, state: T_State, **kwargs: Any) -> Any:
        res = await self.executor.catch(event, state, self.extra["name"], self.extra["type"], self.default)
        if res is not PydanticUndefined:
            return res
        return self.default


class AlconnaParam(Param):
    """Alconna 相关注入参数

    本注入解析事件响应器操作 `AlconnaMatcher` 的响应函数内所需参数。
    """

    def __repr__(self) -> str:
        return f"AlconnaParam(type={self.extra['type']!r})"

    @classmethod
    def _check_param(cls, param: inspect.Parameter, allow_types: tuple[type[Param], ...]) -> Optional["AlconnaParam"]:
        annotation = get_origin(param.annotation)
        if annotation in _Contents:
            annotation = get_args(param.annotation)[0]
        if annotation is CommandResult:
            return cls(..., type=CommandResult)
        if annotation is Arparma:
            return cls(..., type=Arparma)
        if annotation is Alconna:
            return cls(..., type=Alconna)
        if annotation is Duplication:
            return cls(..., type=Duplication)
        if annotation is SelectedExtensions:
            return cls(..., type=SelectedExtensions)
        if inspect.isclass(annotation) and issubclass(annotation, Duplication):
            return cls(..., anno=param.annotation, type=Duplication)
        if inspect.isclass(annotation) and issubclass(annotation, Extension):
            return cls(..., anno=param.annotation, type=Extension)
        if annotation is Match:
            return cls(param.default, name=param.name, type=Match)
        if isinstance(param.default, Query):
            return cls(param.default, type=Query)
        if param.name in ("ctx", "context") and annotation is dict:
            return cls(..., type=Literal["context"])
        return cls(param.default, validate=True, name=param.name, type=param.annotation)

    async def _solve(self, event: Event, state: T_State, **kwargs: Any) -> Any:
        matcher = kwargs.get("matcher", object())
        t = self.extra["type"]
        if ALCONNA_RESULT not in state:
            return self.default if self.default not in (..., Empty) else PydanticUndefined
        res: CommandResult = state[ALCONNA_RESULT]
        if t is CommandResult:
            return res
        if t is Arparma:
            return res.result
        if t is Alconna:
            return res.source
        if t is Duplication:
            if anno := self.extra.get("anno"):
                return anno(res.result)
            return generate_duplication(res.source)(res.result)
        if t is SelectedExtensions:
            return state[ALCONNA_EXTENSION]
        if t is Extension:
            anno = self.extra["anno"]
            return next((i for i in state[ALCONNA_EXTENSION].context if isinstance(i, anno)), None)  # type: ignore
        if t is Match:
            target = res.result.all_matched_args.get(self.extra["name"], Empty)
            return Match(target, target != Empty)
        if t is Query:
            _path = merge_path(self.default.path, getattr(matcher, "basepath", ""))
            q = Query(_path, self.default.result)
            result = res.result.query(q.path, Empty)
            q.available = result != Empty
            if q.available:
                q.result = result
            elif self.default.result != Empty:
                q.available = True
            return q
        if t == Literal["context"]:
            return res.result.context
        keys: list[str] = state.get(ALCONNA_ARG_KEYS, [])
        if (key := self.extra["name"]) in keys:
            return state[ALCONNA_ARG_KEY.format(key=key)]
        if any(k := key for key in keys if key.endswith(f".{self.extra['name']}")):
            return state[ALCONNA_ARG_KEY.format(key=k)]
        if self.extra["name"] in res.result.all_matched_args:
            return res.result.all_matched_args[self.extra["name"]]
        if (
            result := res.result.query(
                f"{merge_path(self.extra['name'], getattr(matcher, 'basepath', ''))}.value", Empty
            )
        ) != Empty:
            return result
        return self.default if self.default not in (..., Empty) else PydanticUndefined


class _Dispatch:
    def __init__(
        self,
        path: str,
        value: Any = _seminal,
        or_not: bool = False,
        additional: Optional[CHECK] = None,
    ):
        self.fn = assign(path, value, or_not, additional)
        self.result = None

    def set(self, arp: AlcResult):
        self.result = arp

    async def __call__(self, _state: T_State, event: Event, bot: Bot) -> bool:
        if self.result is None:
            return False
        if await self.fn(event, bot, _state, self.result.result):
            _state[ALCONNA_RESULT] = self.result
            self.result = None
            return True
        return False


class StackParam(Param):
    """上下文栈注入参数。

    本注入解析 AsyncExitStack 实例，用于在依赖注入中管理异步上下文。
    """

    def __repr__(self) -> str:
        return "_StackParam()"

    @classmethod
    @override
    def _check_param(cls, param: inspect.Parameter, allow_types: tuple[type[Param], ...]) -> Optional[Self]:
        if param.annotation == AsyncExitStack:
            return cls(..., type=AsyncExitStack)
        if param.annotation == Optional[AsyncExitStack]:
            return cls(None, type=AsyncExitStack)
        if generic_check_issubclass(param.annotation, AsyncExitStack):
            return cls(None, type=AsyncExitStack)

    @override
    async def _solve(self, stack: Optional[AsyncExitStack] = None, **kwargs: Any) -> Any:
        return stack


class DependencyCacheParam(Param):
    """依赖缓存注入参数。

    本注入解析 T_DependencyCache 实例，用于在依赖注入中管理依赖缓存。
    """

    def __repr__(self) -> str:
        return "_DependencyCacheParam()"

    @classmethod
    @override
    def _check_param(cls, param: inspect.Parameter, allow_types: tuple[type[Param], ...]) -> Optional[Self]:
        if param.annotation == dict[_DependentCallable[Any], DependencyCache]:
            return cls(..., type=dict[_DependentCallable[Any], DependencyCache])
        if param.annotation == Optional[dict[_DependentCallable[Any], DependencyCache]]:
            return cls(None, type=dict[_DependentCallable[Any], DependencyCache])
        if is_optional(param.annotation, dict[_DependentCallable[Any], DependencyCache]):
            return cls(None, type=dict[_DependentCallable[Any], DependencyCache])

    @override
    async def _solve(
        self, dependency_cache: Optional[dict[_DependentCallable[Any], DependencyCache]] = None, **kwargs: Any
    ) -> Any:
        return dependency_cache
