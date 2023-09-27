import pytest
import nonebot

# 导入适配器
from nonebot.adapters.console import Adapter as ConsoleAdapter
from nonebot.adapters.onebot.v11 import Adapter as Onebot11Adapter


@pytest.fixture(scope="session", autouse=True)
def load_bot():
    # 加载适配器
    driver = nonebot.get_driver()
    driver.register_adapter(ConsoleAdapter)
    driver.register_adapter(Onebot11Adapter)

    nonebot.require("nonebot_plugin_alconna")
    return None
