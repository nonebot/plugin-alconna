import pytest
from nonebug import App
from nonebot import get_adapter
from arclet.alconna import Args, Alconna
from nonebot.adapters.qq import Bot, Adapter, Message, MessageSegment

from tests.fake import fake_message_event_guild


@pytest.mark.asyncio()
async def test_send(app: App):
    from nonebot_plugin_alconna import lang, on_alconna
    from nonebot_plugin_alconna.uniseg.segment import I18n

    cmd = on_alconna(Alconna("test", Args["name", str]))

    lang.load_data(
        "zh-CN",
        {
            "test-i18n": {
                "command.test.1": "测试!",
                "command.test.2": "{:At(user, $event.get_user_id())} 你好!",
                "command.test.3": "这是 {abcd} 测试!",
                "command.test.4": "这是嵌套: {:I18n(test-i18n, command.test.1)}",
            }
        },
    )
    lang.load_data(
        "en-US",
        {
            "test-i18n": {
                "command.test.1": "test!",
                "command.test.2": "{:At(user, $event.get_user_id())} hello!",
                "command.test.3": "This is {abcd} test!",
                "command.test.4": "This is nested: {:I18n(test-i18n, command.test.1)}",
            }
        },
    )

    @cmd.handle()
    async def _():
        await cmd.send(I18n("test-i18n", "command.test.1"))
        await cmd.send(I18n("test-i18n", "command.test.2"))
        await cmd.send(cmd.i18n("test-i18n", "command.test.3", abcd="test"))
        await cmd.finish(cmd.i18n("test-i18n", "command.test.4"))

    lang.select("zh-CN")
    async with app.test_matcher(cmd) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, bot_info=None)
        event = fake_message_event_guild(message=Message("test aaaa"), id="123", user_id="5678")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, Message("测试!"))
        ctx.should_call_send(event, MessageSegment.mention_user("5678") + " 你好!")
        ctx.should_call_send(event, Message("这是 test 测试!"))
        ctx.should_call_send(event, Message("这是嵌套: 测试!"))
        ctx.should_finished()

    lang.select("en-US")
    async with app.test_matcher(cmd) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, bot_info=None)
        event = fake_message_event_guild(message=Message("test aaaa"), id="123", user_id="5678")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, Message("test!"))
        ctx.should_call_send(event, MessageSegment.mention_user("5678") + " hello!")
        ctx.should_call_send(event, Message("This is test test!"))
        ctx.should_call_send(event, Message("This is nested: test!"))
        ctx.should_finished()

    lang.select("zh-CN")
