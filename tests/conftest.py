import pytest
import nonebot
from nonebug import NONEBOT_INIT_KWARGS

# 导入适配器
from nonebot.adapters.discord import Adapter as DiscordAdapter
from nonebot.adapters.onebot.v11 import Adapter as Onebot11Adapter


def pytest_configure(config: pytest.Config):
    config.stash[NONEBOT_INIT_KWARGS] = {"driver": "~fastapi+~httpx+~websockets"}


@pytest.fixture(scope="session", autouse=True)
def load_bot():
    # 加载适配器
    driver = nonebot.get_driver()
    driver.register_adapter(DiscordAdapter)
    driver.register_adapter(Onebot11Adapter)

    nonebot.require("nonebot_plugin_alconna")
    return None
