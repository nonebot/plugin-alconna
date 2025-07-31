import pytest
from nonebug import App
from nonebot import get_adapter
from nonebot.adapters.onebot.v11 import Bot, Adapter, Message

from tests.fake import fake_group_message_event_v11


@pytest.mark.asyncio()
async def test_command(app: App):
    from nonebot_plugin_alconna import Args, Alconna, on_alconna

    alc = Alconna("weather", Args["city#城市名称", str])
    matcher = on_alconna(alc, aliases={"天气"})

    @matcher.handle()
    async def _(city: str):
        await matcher.send(city)

    async with app.test_matcher(matcher) as ctx:  # type: ignore
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("weather abcd"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "abcd")
        event1 = fake_group_message_event_v11(message=Message("天气 abcd"), user_id=123)
        ctx.receive_event(bot, event1)
        ctx.should_call_send(event1, "abcd")
        event2 = fake_group_message_event_v11(message=Message("天气abcd"), user_id=123)
        ctx.receive_event(bot, event2)
        ctx.should_not_pass_rule()
