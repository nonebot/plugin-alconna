from io import BytesIO
from pathlib import Path
from typing import Union

from nonebot import require

from nonebot_plugin_alconna.uniseg.segment import Media

try:
    require("nonebot_plugin_filehost")
    from nonebot_plugin_filehost import FileHost
except ImportError:
    raise ImportError("You need to install nonebot_plugin_filehost to use this module.")


async def to_url(data: Union[str, Path, bytes, BytesIO], bot: ..., name: Union[str, None] = None) -> str:
    if isinstance(data, str):
        data = Path(data)
    return await FileHost(data, filename=name).to_url()


Media.to_url = to_url
