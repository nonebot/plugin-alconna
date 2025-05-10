import pytest
from nonebug import App
from nonebot import get_adapter
from nonebot.adapters.onebot.v11 import Bot, Adapter, Message, MessageSegment

from tests.fake import fake_self_message_event_v11, fake_group_message_event_v11


@pytest.mark.asyncio()
async def test_command(app: App):
    from nonebot_plugin_alconna import Args, Alconna, on_alconna

    alc = Alconna("天气", Args["city#城市名称", str])
    matcher = on_alconna(alc)
    matcher.shortcut("^(?P<city>.+)天气$", {"args": ["{city}"]})

    @matcher.handle()
    async def _(city: str):
        await matcher.send(city)

    async with app.test_matcher(matcher) as ctx:  # type: ignore
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("天气 abcd"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "abcd")
        event1 = fake_group_message_event_v11(message=Message("abcd天气"), user_id=123)
        ctx.receive_event(bot, event1)
        ctx.should_call_send(event1, "abcd")
        ev2 = fake_group_message_event_v11(message=Message([MessageSegment.face(i) for i in range(50)]), user_id=123)
        ctx.receive_event(bot, ev2)
        ctx.should_not_pass_rule(matcher)


@pytest.mark.asyncio()
async def test_sent(app: App):
    from nonebot_plugin_alconna.builtins.extensions.onebot11 import MessageSentExtension
    from nonebot_plugin_alconna import Alconna, AlconnaMatcher, on_alconna, add_global_extension

    add_global_extension(MessageSentExtension())

    mat1 = on_alconna("sent1", response_self=True)
    mat2 = on_alconna("sent2", response_self=False)

    @mat1.handle()
    @mat2.handle()
    async def _(cmd: Alconna, mat: AlconnaMatcher):
        await mat.send(cmd.name)

    async with app.test_matcher(mat1) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, self_id="123")
        event = fake_self_message_event_v11(message=Message("sent1"), user_id=123, self_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "sent1")

    async with app.test_matcher(mat2) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, self_id="123")
        event = fake_self_message_event_v11(message=Message("sent2"), user_id=123, self_id=123)
        ctx.receive_event(bot, event)
        ctx.should_not_pass_rule(mat2)
