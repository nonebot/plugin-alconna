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


async def to_url(img: Union[str, Path, bytes, BytesIO], name: Union[str, None] = None) -> str:
    if isinstance(img, str):
        img = Path(img)
    return await FileHost(img, filename=name).to_url()


Media.to_url = to_url
