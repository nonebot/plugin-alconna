from arclet.alconna import Args, Option, Alconna


def test_fallback():
    import nonebot_plugin_alconna  # noqa: F401

    assert Alconna("test_fallback").parse("test_fallback").matched


def test_v11():
    from nonebot.adapters.onebot.v11 import Message

    import nonebot_plugin_alconna  # noqa: F401
    from nonebot_plugin_alconna.adapters.onebot11 import At, Image

    msg = Message(["Hello!11", At(123)])
    img = Image(b"123")
    assert str(msg) == "Hello!11[CQ:at,qq=123]"

    alc = Alconna("Hello!11", Args["target", At])
    res = alc.parse(msg)
    assert res.matched
    assert res.target.data["qq"] == "123"
    assert not alc.parse(Message(["Hello!11", img])).matched

    alc1 = Alconna(Image)
    assert alc1.parse(Message([img])).header_match.origin == img

    alc2 = Alconna([At(114514)], "chat")
    assert alc2.parse(Message([At(114514), "chat"])).matched
    assert not alc2.parse(Message([At(11454), "chat"])).matched
    assert not alc2.parse(Message([img, "chat"])).matched

    alc3 = Alconna([At], "give")
    assert alc3.parse(Message([At(114514), "give"])).matched
    assert alc3.parse(Message([At(1919810), "give"])).matched
    assert not alc3.parse(Message([img, "give"])).matched


def test_v12():
    from nonebot.adapters.onebot.v12 import Message

    import nonebot_plugin_alconna  # noqa: F401
    from nonebot_plugin_alconna.adapters.onebot12 import Image, Mention

    msg = Message(["Hello!12", Mention("123")])
    img = Image("1.png")
    assert str(msg) == "Hello!12[mention:user_id=123]"

    alc = Alconna("Hello!12", Args["target", Mention])
    res = alc.parse(msg)
    assert res.matched
    assert res.target.data["user_id"] == "123"
    assert not alc.parse(Message(["Hello!", img])).matched

    alc1 = Alconna(Image)
    assert alc1.parse(Message([img])).header_match.origin == img

    alc2 = Alconna([Mention("114514")], "chat")
    assert alc2.parse(Message([Mention("114514"), "chat"])).matched
    assert not alc2.parse(Message([Mention("11454"), "chat"])).matched
    assert not alc2.parse(Message([img, "chat"])).matched

    msg1 = Message("Hello! --foo 123")
    assert str(msg1) == "Hello! --foo 123"

    alc3 = Alconna("Hello!", Option("--foo", Args["foo", int]))
    res1 = alc3.parse(msg1)
    assert res1.matched
    assert res1.query("foo.foo") == 123
    assert not alc3.parse(Message(["Hello!", img])).matched

    alc4 = Alconna([Mention], "give")
    assert alc4.parse(Message([Mention("114514"), "give"])).matched
    assert alc4.parse(Message([Mention("1919810"), "give"])).matched
    assert not alc4.parse(Message([img, "give"])).matched


def test_generic():
    from nonebot.adapters.onebot.v11 import Message as Onebot11Message
    from nonebot.adapters.onebot.v12 import Message as Onebot12Message

    import nonebot_plugin_alconna  # noqa: F401
    from nonebot_plugin_alconna.uniseg import At as GenericAt
    from nonebot_plugin_alconna.adapters.onebot11 import At as Onebot11At
    from nonebot_plugin_alconna.adapters.onebot11 import Image as Onebot11Image
    from nonebot_plugin_alconna.adapters.onebot12 import Image as Onebot12Image
    from nonebot_plugin_alconna.adapters.onebot12 import Mention as Onebot12Mention

    msg11 = Onebot11Message(["Hello!", Onebot11At(123)])
    msg12 = Onebot12Message(["Hello!", Onebot12Mention("123")])
    img11 = Onebot11Image(b"123")
    img12 = Onebot12Image("1.png")
    assert str(msg11) == "Hello![CQ:at,qq=123]"
    assert str(msg12) == "Hello![mention:user_id=123]"

    alc = Alconna("Hello!", Args["target", GenericAt])

    assert alc.parse(msg11).matched
    assert alc.parse(msg12).matched
    assert alc.parse(msg11).target.target == "123"
    assert alc.parse(msg12).target.target == "123"
    assert not alc.parse(Onebot11Message(["Hello!", img11])).matched
    assert not alc.parse(Onebot12Message(["Hello!", img12])).matched
