from typing import Type
from nonebot import get_driver
from arclet.alconna import Alconna
from .rule import alconna, set_converter
from .matcher import on_alconna, match_value, match_path, assign
from .params import AlconnaResult, AlconnaMatch, AlconnaMatches, AlconnaDuplication, AlconnaQuery
from .model import Match, CommandResult, Query
from .analyser import NonebotCommandAnalyser
from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)
Alconna: Type[Alconna[NonebotCommandAnalyser]] = Alconna.default_analyser(NonebotCommandAnalyser)
