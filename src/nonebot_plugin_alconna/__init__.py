from __future__ import annotations

from arclet.alconna import Alconna
from .rule import alconna
from .matcher import on_alconna, match_value, match_path, assign
from .params import AlconnaResult, AlconnaMatch, AlconnaMatches, AlconnaDuplication, AlconnaQuery
from .model import Match, CommandResult, Query
from .analyser import NonebotCommandAnalyser

Alconna: type[Alconna[NonebotCommandAnalyser]] = Alconna.default_analyser(NonebotCommandAnalyser)
