import asyncio

import pytest
from nonebug import App
from nonebot import get_adapter
from arclet.alconna import Args, Alconna
from nonebot.adapters.qq import Bot, Adapter, Message

from tests.fake import fake_message_event_guild


@pytest.mark.asyncio()
async def test_send(app: App):
    from nonebot_plugin_alconna import At, on_alconna

    def check(name: str):
        asyncio.create_task(bot.send(event, "check running"))
        if isinstance(name, str):
            return name
        return None

    cmd = on_alconna(Alconna([At], "test", Args["name", check]))

    @cmd.handle()
    async def _():
        await cmd.finish("test!")

    async with app.test_matcher(cmd) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, bot_info=None)
        event = fake_message_event_guild(message=Message("<@5678> test aaaa"), id="123")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "check running")
        ctx.should_call_send(event, "test!")
        ctx.should_finished()
