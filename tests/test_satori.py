import pytest
from nonebug import App
from nepattern import Dot
from nonebot import get_adapter
from arclet.alconna import Args, Alconna
from nonebot.adapters.satori.element import parse
from nonebot.adapters.satori import Bot, Adapter, Message, MessageSegment

from tests.fake import fake_message_event_satori


def test_message_rollback():
    from nonebot_plugin_alconna import Image, select_first

    text = """\
捏<chronocat:marketface tab-id="237834" face-id="a651cf5813ba41587b22d273682e01ae" key="e08787120cade0a5">
  <img src="http://127.0.0.1:5500/v1/assets/eyJ0eXBlIjoibWF..."/>
</chronocat:marketface>
    """
    msg = Message.from_satori_element(parse(text))

    text1 = '捏<img src="http://127.0.0.1:5500/v1/assets/eyJ0eXBlIjoibWF..." />'

    msg1 = Message.from_satori_element(parse(text1))

    alc = Alconna("捏", Args["img", Dot(select_first(Image), str, "url")])

    res = alc.parse(msg, {"$adapter.name": "Satori"})
    assert res.matched
    assert res.query[str]("img") == "http://127.0.0.1:5500/v1/assets/eyJ0eXBlIjoibWF..."

    res1 = alc.parse(msg1, {"$adapter.name": "Satori"})
    assert res1.matched
    assert res1.query[str]("img") == "http://127.0.0.1:5500/v1/assets/eyJ0eXBlIjoibWF..."


@pytest.mark.asyncio()
async def test_satori(app: App):
    from nonebot_plugin_alconna import Bold, Italic, Underline

    msg = Message("/com<b>mand s<i>ome</i>_arg</b> <u>some_arg</u> <b><i>some_arg</i></b>")

    alc = Alconna("/command", Args["some_arg", Bold]["some_arg1", Underline]["some_arg2", Bold + Italic])

    res = alc.parse(msg, {"$adapter.name": "Satori"})
    assert res.matched
    some_arg = res.some_arg
    assert some_arg.type == "text"
    assert str(some_arg) == "<bold>s<italic>ome</italic>_arg</bold>"
    some_arg1 = res.some_arg1
    assert some_arg1.type == "text"
    assert some_arg1.data["styles"] == {(0, 8): ["underline"]}
    some_arg2 = res.some_arg2
    assert some_arg2.type == "text"
    assert some_arg2.data["styles"] == {(0, 8): ["bold", "italic"]}

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
