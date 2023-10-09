from arclet.alconna import Args, Alconna


def test_satori():
    from nonebot.adapters.satori import Message
    from nonebot_plugin_alconna.adapters.satori import Bold, Underline

    msg = Message("/com<b>mand some_arg</b> <u>some_arg</u> some_arg")

    alc = Alconna("/command", Args["some_arg", Bold]["some_arg1", Underline]["some_arg2", str])

    res = alc.parse(msg)
    assert res.matched
    assert res.some_arg.data["style"] == "b"
    assert res.some_arg1.data["style"] == "u"
    assert isinstance(res.some_arg2, str)

    msg1 = "/command " + Bold("foo bar baz")

    alc1 = Alconna("/command", Args["foo", str]["bar", Bold]["baz", Bold])

    res1 = alc1.parse(msg1)
    assert res1.matched
    assert isinstance(res1.foo, str)
    assert res1.bar.type == "entity"
    assert res1.baz.data["style"] == "b"
