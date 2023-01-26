from __future__ import annotations

from arclet.alconna import Alconna
from .rule import alconna
from .matcher import on_alconna
from .params import AlconnaResult, AlconnaMatch, AlconnaMatches, AlconnaDuplication
from .model import Match, AlconnaCommandResult
from .analyser import NonebotCommandAnalyser

Alconna: type[Alconna[NonebotCommandAnalyser]] = Alconna.default_analyser(NonebotCommandAnalyser)
