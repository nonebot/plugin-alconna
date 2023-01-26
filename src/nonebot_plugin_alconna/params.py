from arclet.alconna import Arparma, Empty
from arclet.alconna.core import T_Duplication
from nonebot.internal.params import Depends as Depends
from nonebot.typing import T_State

from .consts import ALCONNA_RESULT
from .model import AlconnaCommandResult, Match


def _alconna_result(state: T_State) -> AlconnaCommandResult:
    return state[ALCONNA_RESULT]


def AlconnaResult() -> AlconnaCommandResult:
    return Depends(_alconna_result, use_cache=False)


def _alconna_matches(state: T_State) -> Arparma:
    return _alconna_result(state).result


def AlconnaMatches() -> Arparma:
    return Depends(_alconna_result, use_cache=False)


def AlconnaMatch(name: str) -> Match:
    def _alconna_match(state: T_State) -> Match:
        arp = _alconna_result(state).result
        return Match(
            arp.all_matched_args.get(name, Empty), name in arp.all_matched_args
        )

    return Depends(_alconna_match, use_cache=False)


def _alconna_duplication(state: T_State) -> T_Duplication:
    return _alconna_result(state).duplication


def AlconnaDuplication() -> T_Duplication:
    return Depends(_alconna_duplication, use_cache=False)
