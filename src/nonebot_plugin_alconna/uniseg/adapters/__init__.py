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
from ..constraint import SupportAdapter

root = Path(__file__).parent
loaders: dict[str, BaseLoader] = {}
_adapters = [path.stem for path in root.iterdir() if path.is_dir() and not path.stem.startswith("_")]
for name in _adapters:
    try:
        module = importlib.import_module(f".{name}", __package__)
        loader = cast(BaseLoader, module.Loader())
        loaders[loader.get_adapter().value] = loader
    except Exception as e:  # noqa: PERF203
        warn(f"Failed to import uniseg adapter {name}: {e}", RuntimeWarning, 15)

EXPORTER_MAPPING: dict[str, MessageExporter] = {
    SupportAdapter.nonebug.value: loaders[SupportAdapter.nonebug.value].get_exporter()
}
BUILDER_MAPPING: dict[str, MessageBuilder] = {
    SupportAdapter.nonebug.value: loaders[SupportAdapter.nonebug.value].get_builder()
}
FETCHER_MAPPING: dict[str, TargetFetcher] = {}
adapters = {}
try:
    adapters = get_adapters()
except Exception as e:
    warn(f"Failed to get nonebot adapters: {e}", RuntimeWarning, 15)

if os.environ.get("PLUGIN_ALCONNA_TESTENV"):
    for adapter, loader in loaders.items():
        try:
            EXPORTER_MAPPING[adapter] = loader.get_exporter()
            BUILDER_MAPPING[adapter] = loader.get_builder()
            with suppress(NotImplementedError):
                FETCHER_MAPPING[adapter] = loader.get_fetcher()
        except Exception as e:  # noqa: PERF203
            warn(f"Failed to load uniseg adapter {adapter}: {e}", RuntimeWarning, 15)
elif not adapters:
    warn(
        "No adapters found, please make sure you have installed at least one adapter.",
        RuntimeWarning,
        15,
    )
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


def alter_get_exporter(adapter_name: str):
    if adapter_name in EXPORTER_MAPPING:
        return EXPORTER_MAPPING[adapter_name]
    if adapter_name in loaders:
        try:
            EXPORTER_MAPPING[adapter_name] = loaders[adapter_name].get_exporter()
            return EXPORTER_MAPPING[adapter_name]
        except Exception as e:
            warn(f"Failed to load uniseg adapter {adapter_name}: {e}", RuntimeWarning, 6)
            return None
    warn(
        f"Adapter {adapter_name} is not found in the uniseg.adapters,"
        f"please go to the github repo and create an issue for it.",
        RuntimeWarning,
        6,
    )
    return None


def alter_get_builder(adapter_name: str):
    if adapter_name in BUILDER_MAPPING:
        return BUILDER_MAPPING[adapter_name]
    if adapter_name in loaders:
        try:
            BUILDER_MAPPING[adapter_name] = loaders[adapter_name].get_builder()
            return BUILDER_MAPPING[adapter_name]
        except Exception as e:
            warn(f"Failed to load uniseg adapter {adapter_name}: {e}", RuntimeWarning, 6)
            return None
    warn(
        f"Adapter {adapter_name} is not found in the uniseg.adapters,"
        f"please go to the github repo and create an issue for it.",
        RuntimeWarning,
        6,
    )
    return None


def alter_get_fetcher(adapter_name: str):
    if adapter_name in FETCHER_MAPPING:
        return FETCHER_MAPPING[adapter_name]
    if adapter_name in loaders:
        try:
            FETCHER_MAPPING[adapter_name] = loaders[adapter_name].get_fetcher()
            return FETCHER_MAPPING[adapter_name]
        except NotImplementedError:
            return None
        except Exception as e:
            warn(f"Failed to load uniseg adapter {adapter_name}: {e}", RuntimeWarning, 6)
            return None
    warn(
        f"Adapter {adapter_name} is not found in the uniseg.adapters,"
        f"please go to the github repo and create an issue for it.",
        RuntimeWarning,
        6,
    )
    return None
