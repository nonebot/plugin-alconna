from typing import Union

import pytest
from nonebug import App
from nonebot import get_adapter
from arclet.alconna import Args, Alconna
from nonebot.adapters.onebot.v11 import Bot, Adapter, Message, MessageSegment

from tests.fake import fake_group_message_event_v11


@pytest.mark.asyncio()
async def test_got_path(app: App):
    from nonebot_plugin_alconna import At, Match, UniMessage, on_alconna

    test_cmd = on_alconna(Alconna("test", Args["target?", Union[str, At]]))

    @test_cmd.handle()
    async def tt_h(target: Match[Union[str, At]]):
        if target.available:
            test_cmd.set_path_arg("target", target.result)

    @test_cmd.got_path("target", prompt="请输入目标")
    async def tt(target: Union[str, At]):
        await test_cmd.send(UniMessage(["ok\n", target]))

    async with app.test_matcher(test_cmd) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("test"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "请输入目标", result=None)
        ctx.should_rejected(test_cmd)
        event = fake_group_message_event_v11(message=Message("1234"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, Message("ok\n1234"))

        event = fake_group_message_event_v11(message=Message("test"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "请输入目标", result=None)
        ctx.should_rejected(test_cmd)
        event = fake_group_message_event_v11(message=Message(MessageSegment.at(1234)), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, Message([MessageSegment.text("ok\n"), MessageSegment.at(1234)]))

        event = fake_group_message_event_v11(message=Message("test 1234"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, Message("ok\n1234"))
