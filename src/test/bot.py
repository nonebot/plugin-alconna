import nonebot
from nonebot.adapters.console import Adapter as ConsoleAdapter
nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(ConsoleAdapter)

nonebot.load_plugin("plugins.demo")

if __name__ == "__main__":
    nonebot.run()
