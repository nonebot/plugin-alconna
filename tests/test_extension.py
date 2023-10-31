from typing import Any

import pytest
from nonebug import App
from nonebot import get_adapter
from arclet.alconna import Args, Alconna
from nonebot.adapters.onebot.v11 import Bot, Adapter, Message

from tests.fake import fake_group_message_event_v11


@pytest.mark.asyncio()
async def test_extension(app: App):
    from nonebot.adapters.onebot.v11 import MessageEvent

    from nonebot_plugin_alconna import Extension, Interface, on_alconna

    class DemoExtension(Extension):
        @property
        def priority(self) -> int:
            return 1

        @property
        def id(self) -> str:
            return "demo"

        async def permission_check(self, bot, event, command):
            if event.get_user_id() != "123":
                await bot.send(event, "权限不足！")
                return False
            return True

        def before_catch(self, name: str, annotation: Any, default: Any) -> bool:
            if annotation is str:
                return True
            return False

        async def catch(self, interface: Interface[MessageEvent]):
            if interface.annotation is str:
                return {
                    "hello": "Hello!",
                    "world": "World!",
                }.get(interface.name, interface.name)

    add = on_alconna(Alconna("add", Args["a", float]["b", float]), extensions=[DemoExtension], comp_config={})

    @add.handle()
    async def h(a: float, b: float, hello: str, world: str, test: str):
        """加法测试"""
        await add.send(f"{a} + {b} = {a + b}\n{hello} {world} {test}!")

    async with app.test_matcher(add) as ctx:  # type: ignore
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("add 1.3 2.4"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "1.3 + 2.4 = 3.7\nHello! World! test!")

        event = fake_group_message_event_v11(message=Message("add 1.3 2.4"), user_id=456)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "权限不足！")
