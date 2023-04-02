from typing import Optional, Type, TypeVar, overload
from typing_extensions import Annotated

from arclet.alconna import Arparma, Duplication, Empty
from arclet.alconna.duplication import generate_duplication
from nonebot.internal.params import Depends as Depends
from nonebot.typing import T_State

from .consts import ALCONNA_RESULT
from .model import CommandResult, Match, Query, T

T_Duplication = TypeVar("T_Duplication", bound=Duplication)


def _alconna_result(state: T_State) -> CommandResult:
    return state[ALCONNA_RESULT]


def AlconnaResult() -> CommandResult:
    return Depends(_alconna_result, use_cache=False)


def _alconna_matches(state: T_State) -> Arparma:
    return _alconna_result(state).result


def AlconnaMatches() -> Arparma:
    return Depends(_alconna_matches, use_cache=False)


def AlconnaMatch(name: str) -> Match:
    def _alconna_match(state: T_State) -> Match:
        arp = _alconna_result(state).result
        return Match(
            arp.all_matched_args.get(name, Empty), name in arp.all_matched_args
        )

    return Depends(_alconna_match, use_cache=False)


def AlconnaQuery(path: str, default: T = Empty) -> Query[T]:
    def _alconna_query(state: T_State) -> Query:
        arp = _alconna_result(state).result
        q = Query(path, default)
        result = arp.query(path, Empty)
        q.available = result != Empty
        if q.available:
            q.result = result
        elif default != Empty:
            q.available = True
        return q

    return Depends(_alconna_query, use_cache=False)


@overload
def AlconnaDuplication() -> Duplication:
    ...


@overload
def AlconnaDuplication(__t: Type[T_Duplication]) -> T_Duplication:
    ...


def AlconnaDuplication(__t: Optional[Type[T_Duplication]] = None) -> Duplication:
    def _alconna_match(state: T_State) -> Duplication:
        arp = _alconna_result(state).result
        return __t(arp) if __t else generate_duplication(arp)

    return Depends(_alconna_match, use_cache=False)


AlcResult = Annotated[CommandResult, AlconnaResult()]
AlcMatches = Annotated[Arparma, AlconnaMatches()]
