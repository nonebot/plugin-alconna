from typing_extensions import NotRequired
from typing import Union, Generic, Literal, TypeVar, Optional, TypedDict

from pydantic import Field, BaseModel
from arclet.alconna import Empty, Alconna, Arparma
from arclet.alconna.duplication import Duplication
from nonebot.compat import PYDANTIC_V2, ConfigDict

T = TypeVar("T")
T_Duplication = TypeVar("T_Duplication", bound=Duplication)


class Match(Generic[T]):
    """
    匹配项，表示参数是否存在于 `all_matched_args` 内
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
    source: Alconna
    result: Arparma
    output: Optional[str] = Field(default=None)

    @property
    def matched(self) -> bool:
        return self.result.matched

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
