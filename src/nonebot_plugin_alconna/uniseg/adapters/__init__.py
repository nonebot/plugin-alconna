import os
import importlib
from pathlib import Path
from warnings import warn
from typing import Dict, cast

from nonebot import get_adapters

from ..loader import BaseLoader
from ..builder import MessageBuilder
from ..exporter import MessageExporter

root = Path(__file__).parent
loaders: Dict[str, BaseLoader] = {}
_adapters = [path.stem for path in root.iterdir() if path.is_dir() and not path.stem.startswith("_")]
for name in _adapters:
    try:
        module = importlib.import_module(f".{name}", __package__)
        loader = cast(BaseLoader, getattr(module, "Loader"))
        loaders[loader.get_adapter()] = loader
    except Exception as e:
        warn(f"Failed to load adapter {name}: {e}", RuntimeWarning, 15)

try:
    adapters = get_adapters()
except Exception as e:
    warn(f"Failed to load adapters: {e}", RuntimeWarning, 15)
    adapters = {}
EXPORTER_MAPPING: Dict[str, MessageExporter] = {}
BUILDER_MAPPING: Dict[str, MessageBuilder] = {}

if not adapters or os.environ.get("PLUGIN_ALCONNA_TESTENV"):
    warn(
        "No adapters found, please make sure you have installed at least one adapter and have it configured properly.",
        RuntimeWarning,
        15,
    )
    for adapter, loader in loaders.items():
        try:
            EXPORTER_MAPPING[adapter] = loaders[adapter].get_exporter()
            BUILDER_MAPPING[adapter] = loaders[adapter].get_builder()
        except Exception as e:
            warn(f"Failed to load adapter {adapter}: {e}", RuntimeWarning, 15)
else:
    for adapter in adapters:
        if adapter in loaders:
            try:
                EXPORTER_MAPPING[adapter] = loaders[adapter].get_exporter()
                BUILDER_MAPPING[adapter] = loaders[adapter].get_builder()
            except Exception as e:
                warn(f"Failed to load adapter {adapter}: {e}", RuntimeWarning, 15)
        else:
            warn(
                f"Adapter {adapter} is not found in the uniseg.adapters,"
                f"please go to the github repo and create an issue for it.",
                RuntimeWarning,
                15,
            )
