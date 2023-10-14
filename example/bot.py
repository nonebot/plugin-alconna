import nonebot
from nonebot.adapters.onebot.v12 import Adapter as ONEBOT_V12Adapter
from nonebot.adapters.red import Adapter as REDAdapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V12Adapter)
driver.register_adapter(REDAdapter)

# nonebot.require("nonebot_plugin_alconna")
nonebot.load_plugin("plugins.demo")

if __name__ == "__main__":
    nonebot.run()
