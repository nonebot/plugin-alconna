import os
import importlib
from typing import cast
from pathlib import Path
from warnings import warn
from contextlib import suppress

from nonebot import get_adapters

from ..loader import BaseLoader
from ..target import TargetFetcher
from ..builder import MessageBuilder
from ..exporter import MessageExporter

root = Path(__file__).parent
loaders: dict[str, BaseLoader] = {}
_adapters = [path.stem for path in root.iterdir() if path.is_dir() and not path.stem.startswith("_")]
for name in _adapters:
    try:
        module = importlib.import_module(f".{name}", __package__)
        loader = cast(BaseLoader, getattr(module, "Loader")())
        loaders[loader.get_adapter().value] = loader
    except Exception as e:
        warn(f"Failed to import uniseg adapter {name}: {e}", RuntimeWarning, 15)

EXPORTER_MAPPING: dict[str, MessageExporter] = {}
BUILDER_MAPPING: dict[str, MessageBuilder] = {}
FETCHER_MAPPING: dict[str, TargetFetcher] = {}

try:
    adapters = get_adapters()
except Exception as e:
    warn(f"Failed to get nonebot adapters: {e}", RuntimeWarning, 15)
else:
    if not adapters:
        warn(
            "No adapters found, please make sure you have installed at least one adapter.",
            RuntimeWarning,
            15,
        )
    elif os.environ.get("PLUGIN_ALCONNA_TESTENV"):
        for adapter, loader in loaders.items():
            try:
                EXPORTER_MAPPING[adapter] = loaders[adapter].get_exporter()
                BUILDER_MAPPING[adapter] = loaders[adapter].get_builder()
                with suppress(NotImplementedError):
                    FETCHER_MAPPING[adapter] = loaders[adapter].get_fetcher()
            except Exception as e:
                warn(f"Failed to load uniseg adapter {adapter}: {e}", RuntimeWarning, 15)
    else:
        for adapter in adapters:
            if adapter in loaders:
                try:
                    EXPORTER_MAPPING[adapter] = loaders[adapter].get_exporter()
                    BUILDER_MAPPING[adapter] = loaders[adapter].get_builder()
                    with suppress(NotImplementedError):
                        FETCHER_MAPPING[adapter] = loaders[adapter].get_fetcher()
                except Exception as e:
                    warn(f"Failed to load uniseg adapter {adapter}: {e}", RuntimeWarning, 15)
            else:
                warn(
                    f"Adapter {adapter} is not found in the uniseg.adapters,"
                    f"please go to the github repo and create an issue for it.",
                    RuntimeWarning,
                    15,
                )
