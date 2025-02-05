import os
from typing import Any

import pytest
import nonebot
from nonebug import NONEBOT_INIT_KWARGS
from pytest_asyncio import is_async_test

# 导入适配器
from nonebot.adapters.qq import Adapter as QQAdapter
from nonebot.adapters.satori import Adapter as SatoriAdapter
from nonebot.adapters.discord import Adapter as DiscordAdapter
from nonebot.adapters.onebot.v11 import Adapter as Onebot11Adapter
from nonebot.adapters.onebot.v12 import Adapter as Onebot12Adapter


def pytest_configure(config: pytest.Config):
    config.stash[NONEBOT_INIT_KWARGS] = {
        "driver": "~fastapi+~httpx+~websockets",
        "log_level": "DEBUG",
        "host": "127.0.0.1",
        "port": "9555",
        "filehost_host_override": "http://filehost.example.com",
    }
    os.environ["PLUGIN_ALCONNA_TESTENV"] = "1"


def pytest_collection_modifyitems(items: Any) -> None:
    """
    Make all tests run on the same event loop.

    See: https://pytest-asyncio.readthedocs.io/en/latest/how-to-guides/run_session_tests_in_same_loop.html
    """
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture(scope="session", autouse=True)
async def after_nonebot_init(after_nonebot_init: None):
    # 加载适配器
    driver = nonebot.get_driver()
    driver.register_adapter(QQAdapter)
    driver.register_adapter(DiscordAdapter)
    driver.register_adapter(Onebot11Adapter)
    driver.register_adapter(Onebot12Adapter)
    driver.register_adapter(SatoriAdapter)

    nonebot.require("nonebot_plugin_alconna")
    nonebot.require("nonebot_plugin_filehost")
