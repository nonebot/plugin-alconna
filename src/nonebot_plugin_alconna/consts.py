from pathlib import Path
from typing import Literal

from tarina import lang

lang.load(Path(__file__).parent / "i18n")
ALCONNA_RESULT: Literal["_alc_result"] = "_alc_result"
ALCONNA_EXEC_RESULT: Literal["_alc_exec_result"] = "_alc_exec_result"
