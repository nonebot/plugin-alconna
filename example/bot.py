import nonebot
from nonebot.adapters.satori import Adapter as SatoriAdapter
from nonebot.adapters.onebot.v12 import Adapter as ONEBOT_V12Adapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V12Adapter)
driver.register_adapter(SatoriAdapter)

# nonebot.require("nonebot_plugin_alconna")
nonebot.load_plugin("plugins.demo")


async def _():
    from nonebot_plugin_alconna import Target, UniMessage

    await Target.group("123456789", platform=ONEBOT_V12Adapter).send(UniMessage.image(path="test.png"))


if __name__ == "__main__":
    nonebot.run()
