from arclet.alconna import Alconna, Args, Option


def test_v11():
    from nonebot_plugin_alconna.adapters.onebot11 import At, Image
    from nonebot.adapters.onebot.v11 import Message

    msg = MessageChain(["Hello!11", At(123)])
    img = Image(b'123')
    print(msg)

    alc = Alconna("Hello!11", Args["target", At])
    res = alc.parse(msg)
    assert res.matched
    assert res.target.data['qq'] == '123'
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
    from nonebot_plugin_alconna.adapters.onebot12 import Mention, Image
    from nonebot.adapters.onebot.v12 import Message

    msg = Message(["Hello!12", Mention("123")])
    img = Image("1.png")
    print(msg)

    alc = Alconna("Hello!12", Args["target", Mention])
    res = alc.parse(msg)
    assert res.matched
    assert res.target.data['user_id'] == '123'
    assert not alc.parse(Message(["Hello!", img])).matched

    alc1 = Alconna(Image)
    assert alc1.parse(Message([img])).header_match.origin == img

    alc2 = Alconna([Mention('114514')], "chat")
    assert alc2.parse(Message([Mention('114514'), "chat"])).matched
    assert not alc2.parse(Message([Mention('11454'), "chat"])).matched
    assert not alc2.parse(Message([img, "chat"])).matched

    msg1 = Message("Hello! --foo 123")
    print(msg1)

    alc3 = Alconna("Hello!", Option("--foo", Args["foo", int]))
    res1 = alc3.parse(msg1)
    assert res1.matched
    assert res1.query("foo.foo") == 123
    assert not alc3.parse(Message(["Hello!", img])).matched

    alc4 = Alconna([Mention], "give")
    assert alc4.parse(Message([Mention('114514'), "give"])).matched
    assert alc4.parse(Message([Mention('1919810'), "give"])).matched
    assert not alc4.parse(Message([img, "give"])).matched


test_v11()
test_v12()
