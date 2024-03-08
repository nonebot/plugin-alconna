from arclet.alconna import Args, Alconna


def test_tg():
    from nonebot.adapters.telegram.message import Entity

    from nonebot_plugin_alconna import Bold, Text, Underline

    msg = "/com" + Entity.bold("mand some_arg") + " " + Entity.underline("some_arg ") + "some_arg"

    alc = Alconna("/command", Args["some_arg", Bold]["some_arg1", Underline]["some_arg2", str])

    res = alc.parse(msg, {"$adapter.name": "Telegram"})
    assert res.matched
    assert isinstance(res.some_arg, Text)
    assert str(res.some_arg) == "<bold>some_arg</bold>"
    assert isinstance(res.some_arg1, Text)
    assert isinstance(res.some_arg2, str)

    msg1 = "/command " + Entity.bold("foo bar baz")

    alc1 = Alconna("/command", Args["foo", str]["bar", Bold]["baz", Bold])

    res1 = alc1.parse(msg1, {"$adapter.name": "Telegram"})
    assert res1.matched
    assert isinstance(res1.foo, str)
    assert isinstance(res1.bar, Text)
    assert res1.baz.text == "baz"
