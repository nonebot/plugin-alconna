from typing_extensions import TypedDict, NotRequired
from typing import Any, Union, Generic, Literal, TypeVar, Optional

from pydantic import Field, BaseModel
from arclet.alconna.action import Action
from arclet.alconna import Empty, Alconna, Arparma
from arclet.alconna.duplication import Duplication
from nonebot.compat import PYDANTIC_V2, ConfigDict

T = TypeVar("T")
T_Duplication = TypeVar("T_Duplication", bound=Duplication)


class Match(Generic[T]):
    """
    匹配项，表示参数是否存在于 `all_matched_args` 内

    Attributes:
        result (T): 匹配结果
        available (bool): 匹配状态
    """

    result: T
    available: bool

    def __init__(self, result: T, available: bool):
        self.result = result
        self.available = available

    def __repr__(self):
        return f"Match({self.result}, {self.available})"


class Query(Generic[T]):
    """
    查询项，表示参数是否可由 `Arparma.query` 查询并获得结果

    Attributes:
        result (T): 查询结果
        available (bool): 查询状态
        path (str): 查询路径
    """

    result: T
    available: bool
    path: str

    def __init__(self, path: str, default: Union[T, type[Empty]] = Empty):
        self.path = path
        self.result = default  # type: ignore
        self.available = False

    def __repr__(self):
        return f"Query({self.path}, {self.result})"


class CommandResult(BaseModel):
    result: Arparma
    output: Optional[str] = Field(default=None)

    @property
    def source(self) -> Alconna:
        return self.result.source

    @property
    def matched(self) -> bool:
        return self.result.matched

    @property
    def context(self):
        return self.result.context

    if PYDANTIC_V2:
        model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)  # type: ignore
    else:

        class Config:
            frozen = True
            arbitrary_types_allowed = True


class CompConfig(TypedDict):
    tab: NotRequired[str]
    enter: NotRequired[str]
    exit: NotRequired[str]
    timeout: NotRequired[int]
    hide_tabs: NotRequired[bool]
    hides: NotRequired[set[Literal["tab", "enter", "exit"]]]
    disables: NotRequired[set[Literal["tab", "enter", "exit"]]]
    lite: NotRequired[bool]


class SubcommandModel(BaseModel):
    name: str
    default: Any = Empty


class OptionModel(BaseModel):
    name: str
    opt: Optional[str] = None
    default: Any = Empty
    action: Optional[Union[Literal["store_true", "store_false", "count", "append"], Action]] = None


class ShortcutModel(BaseModel):
    key: str
    command: Optional[str] = None
    args: Optional[list[str]] = None
    fuzzy: bool = True
    prefix: bool = False
    humanized: Optional[str] = None


class ActionModel(BaseModel):
    params: list[str]
    code: str

    def gen_exec(self, _globals: dict):
        code = f"async def _({', '.join(self.params)}):"
        lines = self.code.splitlines()
        for line in lines:
            code += f"    {line}"
        _locals = {}
        exec(code, _globals, _locals)
        return _locals["_"]


class CommandModel(BaseModel):
    command: str
    help: Optional[str] = None
    usage: Optional[str] = None
    examples: Optional[list[str]] = None
    author: Optional[str] = None
    fuzzy_match: bool = False
    fuzzy_threshold: float = 0.6
    raise_exception: bool = False
    hide: bool = False
    hide_shortcut: bool = False
    keep_crlf: bool = False
    compact: bool = False
    strict: bool = True
    context_style: Optional[Literal["bracket", "parentheses"]] = None
    extra: Optional[dict[str, Any]] = None

    namespace: Optional[str] = None
    aliases: set[str] = Field(default_factory=set)

    options: list[OptionModel] = Field(default_factory=list)
    subcommands: list[SubcommandModel] = Field(default_factory=list)
    shortcuts: list[ShortcutModel] = Field(default_factory=list)
    actions: list[ActionModel] = Field(default_factory=list)
