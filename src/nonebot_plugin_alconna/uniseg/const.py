from pathlib import Path

from tarina import lang
from nonebot.utils import logger_wrapper

lang.load(Path(__file__).parent / "i18n")
log = logger_wrapper("Plugin-Uniseg")
