import importlib
from pathlib import Path
from warnings import warn
from typing import Dict, cast

from nonebot import get_adapters

from nonebot_plugin_alconna.uniseg.exporter import MessageExporter

from ..loader import BaseLoader

root = Path(__file__).parent
loaders: Dict[str, BaseLoader] = {}
_adapters = [path.stem for path in root.iterdir() if path.is_dir()]
for name in _adapters:
    try:
        module = importlib.import_module(f".{name}", __package__)
        loader = cast(BaseLoader, getattr(module, "Loader"))
        loaders[loader.get_adapter()] = loader
    except Exception as e:
        warn(f"Failed to load adapter {name}: {e}", RuntimeWarning, 15)

adapters = get_adapters()
if not adapters:
    warn(
        "No adapters found, please make sure you have installed at least one adapter and have it configured properly.",
        RuntimeWarning,
        15,
    )
    MAPPING: Dict[str, MessageExporter] = {loader.get_adapter(): loader.get_exporter() for loader in loaders.values()}
else:
    MAPPING: Dict[str, MessageExporter] = {}
    for adapter in adapters:
        if adapter in loaders:
            MAPPING[adapter] = loaders[adapter].get_exporter()
        else:
            warn(
                f"Adapter {adapter} is not found in the uniseg.adapters,"
                f"please go to the github repo and create an issue for it.",
                RuntimeWarning,
                15,
            )
