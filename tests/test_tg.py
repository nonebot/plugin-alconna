from nepattern import type_parser
from arclet.alconna import Args, Alconna


def test_tg():
    from nonebot_plugin_alconna import Image
    from nonebot_plugin_alconna.adapters.telegram import Bold, Photo, Underline

    msg = "/com" + Bold("mand some_arg") + " " + Underline("some_arg ") + "some_arg"

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

    _img = type_parser(Image)
    assert _img.exec(Photo("1")).value == Image(id="1")
