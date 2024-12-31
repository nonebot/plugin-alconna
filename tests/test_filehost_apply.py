import pytest
from nonebug import App
from nonebot import get_adapter
from arclet.alconna import Alconna
from nonebot.adapters.satori import Bot, Adapter, Message, MessageSegment

from tests.fake import fake_satori_bot_params, fake_message_event_satori


@pytest.mark.asyncio()
async def test_patch(app: App):
    from nonebot_plugin_alconna import Image, on_alconna, apply_filehost

    test_cmd = on_alconna(Alconna("test"))

    @test_cmd.handle()
    async def tt_h():
        await test_cmd.send(Image(raw=b"PNG123", name="test.png"))

    dispose = apply_filehost()
    async with app.test_matcher(test_cmd) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, **fake_satori_bot_params())
        msg = Message("test")
        event = fake_message_event_satori(message=msg, id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            Message(MessageSegment.image("http://filehost.example.com/filehost/test.png")),
        )

    dispose()
