from typing import Literal

import pytest
from nonebug import App
from nonebot import get_adapter
from nonebot.adapters.onebot.v11 import Bot, Adapter, Message

from tests.fake import fake_group_message_event_v11


@pytest.mark.asyncio()
async def test_funcommand(app: App):
    from nonebot_plugin_alconna import funcommand

    table = {
        "add": float.__add__,
        "sub": float.__sub__,
        "mul": float.__mul__,
        "div": float.__truediv__,
    }

    @funcommand()
    async def calc(op: Literal["add", "sub", "mul", "div"], a: float, b: float):
        """加法测试"""
        return f"{a} {op} {b} = {table[op](a, b)}"

    async with app.test_matcher(calc) as ctx:  # type: ignore
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("calc add 1.3 2.4"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "1.3 add 2.4 = 3.7")
