import nonebot
from nonebot.adapters.qq import Adapter as QQAdapter
from nonebot.adapters.onebot.v12 import Adapter as ONEBOT_V12Adapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V12Adapter)
driver.register_adapter(QQAdapter)

# nonebot.require("nonebot_plugin_alconna")
nonebot.load_plugin("plugins.demo")


async def _():
    from nonebot_plugin_alconna import Target, UniMessage

    await Target("123456789", platform=ONEBOT_V12Adapter.get_name()).send(UniMessage.image(path="test.png"))


if __name__ == "__main__":
    nonebot.run()
