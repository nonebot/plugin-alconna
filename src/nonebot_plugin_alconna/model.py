from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from arclet.alconna import Arparma, command_manager
from arclet.alconna.core import T_Duplication

T = TypeVar("T")


@dataclass
class Match(Generic[T]):
    """
    匹配项，表示参数是否存在于 `all_matched_args` 内
    result (T): 匹配结果
    available (bool): 匹配状态
    """

    result: T
    available: bool


@dataclass(frozen=True)
class AlconnaCommandResult:
    token: int
    output: str | None = field(default=None)
    duplication_type: type[T_Duplication] | None = field(default=None)

    @property
    def result(self) -> Arparma:
        return command_manager.get_record(self.token)  # type: ignore

    @property
    def matched(self) -> bool:
        return self.result.matched

    @property
    def duplication(self) -> T_Duplication:
        return self.result.get_duplication(self.duplication_type)
