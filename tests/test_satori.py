import pytest
from nonebug import App
from nonebot import get_adapter
from arclet.alconna import Args, Alconna
from nonebot.adapters.satori import Bot, Adapter, Message, MessageSegment

from tests.fake import fake_message_event_satori


def test_satori():
    from nonebot.adapters.satori import Message

    from nonebot_plugin_alconna.adapters.satori import Bold, Underline

    msg = Message("/com<b>mand some_arg</b> <u>some_arg</u> some_arg")

    alc = Alconna("/command", Args["some_arg", Bold]["some_arg1", Underline]["some_arg2", str])

    res = alc.parse(msg)
    assert res.matched
    assert res.some_arg.type == "bold"
    assert res.some_arg1.type == "underline"
    assert isinstance(res.some_arg2, str)

    msg1 = "/command " + Bold("foo bar baz")

    alc1 = Alconna("/command", Args["foo", str]["bar", Bold]["baz", Bold])

    res1 = alc1.parse(msg1)
    assert res1.matched
    assert isinstance(res1.foo, str)
    assert res1.bar.type == "bold"
    assert res1.baz.data["text"] == "baz"


@pytest.mark.asyncio()
async def test_send(app: App):
    from nonebot_plugin_alconna import Text, Image, on_alconna

    test_cmd = on_alconna(Alconna("test", Args["img", Image]))

    @test_cmd.handle()
    async def tt_h(img: Image):
        await test_cmd.send(Text("ok\n") + img)

    async with app.test_matcher(test_cmd) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, platform="satori", info=None)
        msg = "test" + MessageSegment.image(raw={"data": b"123", "mime": "image/png"})
        event = fake_message_event_satori(message=msg, id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, Message('ok\n<img src="data:image/png;base64,MTIz" />'))
