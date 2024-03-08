import pytest
from nonebug import App
from nonebot import get_adapter
from arclet.alconna import Args, Alconna
from nonebot.adapters.satori import Bot, Adapter, Message, MessageSegment

from tests.fake import fake_message_event_satori


@pytest.mark.asyncio()
async def test_satori(app: App):
    from nonebot.adapters.satori import Message

    from nonebot_plugin_alconna import Bold, Text, Underline, on_alconna

    msg = Message("/com<b>mand s<i>ome</i>_arg</b> <u>some_arg</u> some_arg")

    alc = Alconna("/command", Args["some_arg", Bold]["some_arg1", Underline]["some_arg2", str])

    res = alc.parse(msg, {"$adapter.name": "Satori"})
    assert res.matched
    some_arg = res.some_arg
    assert some_arg.type == "text"
    assert str(some_arg) == "<bold>s<italic>ome</italic>_arg</bold>"
    some_arg1 = res.some_arg1
    assert some_arg1.type == "text"
    assert some_arg1.data["styles"] == {(0, 8): ["underline"]}
    assert isinstance(res.some_arg2, str)

    msg1 = "/command " + Bold("foo bar baz")

    alc1 = Alconna("/command", Args["foo", str]["bar", Bold]["baz", Bold])

    res1 = alc1.parse(msg1)
    assert res1.matched
    assert isinstance(res1.foo, str)
    assert res1.bar.type == "text"
    assert res1.baz.data["text"] == "baz"

    msg2 = "/command " + Bold("foo bar baz")

    alc2 = Alconna("/command", Args["foo", str]["bar", Bold]["baz", Underline])
    assert not alc2.parse(msg2).matched

    echo = on_alconna(Alconna("echo", Args["text", Text]))

    @echo.handle()
    async def echo_h(text: Text):
        await echo.send(text)

    async with app.test_matcher(echo) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, platform="satori", info=None)
        event = fake_message_event_satori(message=Message("ec<b>ho h<i>el</i>lo</b>"), id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, Message("<b>h<i>el</i>lo</b>"))


@pytest.mark.asyncio()
async def test_send(app: App):
    from nonebot_plugin_alconna import Text, Image, on_alconna

    test_cmd = on_alconna(Alconna("test", Args["img", Image]))

    @test_cmd.handle()
    async def tt_h(img: Image):
        await test_cmd.send(Text("ok") + img)

    async with app.test_matcher(test_cmd) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, platform="satori", info=None)
        msg = "test" + MessageSegment.image(raw=b"123", mime="image/png")
        event = fake_message_event_satori(message=msg, id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, Message('ok<img src="data:image/png;base64,MTIz" />'))
