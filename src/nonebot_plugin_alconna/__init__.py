from typing import Type
from arclet.alconna import Alconna
from .rule import alconna, set_output_converter
from .matcher import on_alconna, match_value, match_path, assign
from .params import AlconnaResult, AlconnaMatch, AlconnaMatches, AlconnaDuplication, AlconnaQuery
from .model import Match, CommandResult, Query
from .analyser import NonebotCommandAnalyser

Alconna: Type[Alconna[NonebotCommandAnalyser]] = Alconna.default_analyser(NonebotCommandAnalyser)
