from pathlib import Path
from typing import Literal

from tarina import lang
from nonebot.utils import logger_wrapper

lang.load(Path(__file__).parent / "i18n")
ALCONNA_RESULT: Literal["_alc_result"] = "_alc_result"
ALCONNA_EXEC_RESULT: Literal["_alc_exec_result"] = "_alc_exec_result"
ALCONNA_ARG_KEY: Literal["_alc_arg_{key}"] = "_alc_arg_{key}"
ALCONNA_EXTENSION: Literal["_alc_extension"] = "_alc_extension"

log = logger_wrapper("Plugin-Alconna")
