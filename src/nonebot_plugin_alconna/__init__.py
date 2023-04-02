from typing import Type

from arclet.alconna import Alconna

from .analyser import NonebotCommandAnalyser
from .matcher import assign, match_path, match_value, on_alconna
from .model import CommandResult, Match, Query
from .params import (
    AlcMatches,
    AlconnaDuplication,
    AlconnaMatch,
    AlconnaMatches,
    AlconnaQuery,
    AlconnaResult,
    AlcResult,
)
from .rule import alconna, set_output_converter

Alconna: Type[Alconna[NonebotCommandAnalyser]] = Alconna.default_analyser(
    NonebotCommandAnalyser
)
