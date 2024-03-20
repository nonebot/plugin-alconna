import pytest
from nonebug import App
from nonebot.adapters.satori.models import User
from nonebot.adapters.satori import Bot, Message
from arclet.alconna import Args, Alconna, CommandMeta

from tests.fake import fake_message_event_satori


@pytest.mark.asyncio()
async def test_ctx(app: App):
    from nonebot_plugin_alconna import on_alconna

    test_cmd = on_alconna(Alconna("test", Args["userid", str], meta=CommandMeta(context_style="parentheses")))

    @test_cmd.handle()
    async def tt_h(userid: str, ctx: dict):
        assert ctx["event"].get_user_id() == userid
        await test_cmd.send(f"ok\n{userid}")

    async with app.test_matcher(test_cmd) as ctx:
        # adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, platform="satori", info=None)
        msg = Message("test $(event.get_user_id())")
        event = fake_message_event_satori(message=msg, id=123, user=User(id="456", name="test"))
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "ok\n456")
