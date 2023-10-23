import pytest
import nonebot
from nonebug import NONEBOT_INIT_KWARGS

# 导入适配器
from nonebot.adapters.qq import Adapter as QQAdapter
from nonebot.adapters.satori import Adapter as SatoriAdapter
from nonebot.adapters.discord import Adapter as DiscordAdapter
from nonebot.adapters.onebot.v11 import Adapter as Onebot11Adapter


def pytest_configure(config: pytest.Config):
    config.stash[NONEBOT_INIT_KWARGS] = {
        "driver": "~fastapi+~httpx+~websockets",
        "log_level": "DEBUG",
    }


@pytest.fixture(scope="session", autouse=True)
def load_bot():
    # 加载适配器
    driver = nonebot.get_driver()
    driver.register_adapter(QQAdapter)
    driver.register_adapter(DiscordAdapter)
    driver.register_adapter(Onebot11Adapter)
    driver.register_adapter(SatoriAdapter)

    nonebot.require("nonebot_plugin_alconna")
    return None
