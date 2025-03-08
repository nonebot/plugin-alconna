import pytest
from nonebug import App
from nonebot import get_adapter
from arclet.alconna import Alconna
from nonebot.adapters.satori import Bot, Adapter, Message

from tests.fake import fake_satori_bot_params, fake_message_event_satori


@pytest.mark.asyncio()
async def test_use_origin(app: App):
    from nonebot_plugin_alconna import on_alconna

    test_cmd = on_alconna(Alconna("log"), use_origin=False)
    test_cmd1 = on_alconna(Alconna("ALClog"), use_origin=True)

    @test_cmd.handle()
    async def _():
        await test_cmd.send("ok")

    @test_cmd1.handle()
    async def _():
        await test_cmd1.send("ok1")

    async with app.test_matcher([test_cmd, test_cmd1]) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, **fake_satori_bot_params())
        event = fake_message_event_satori(message=Message("log"), original_message=Message("ALClog"), id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "ok")
        ctx.should_call_send(event, "ok1")
