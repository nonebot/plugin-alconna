from arclet.alconna import Alconna, Args, Option


def test_v11():
    from nonebot_plugin_alconna.adapters.onebot11 import At, Image
    from nonebot.adapters.onebot.v11 import Message, MessageSegment

    msg = Message(["Hello!11", MessageSegment.at(123)])
    img = MessageSegment.image(b'123')
    print(msg)

    alc = Alconna("Hello!11", Args["target", At])
    res = alc.parse(msg)
    assert res.matched
    assert res.target.data['qq'] == '123'
    assert not alc.parse(Message(["Hello!11", img])).matched

    alc1 = Alconna(Image)
    assert alc1.parse(Message([img])).header_match.origin == img

    alc2 = Alconna([MessageSegment.at(114514)], "chat")
    assert alc2.parse(Message([MessageSegment.at(114514), "chat"])).matched
    assert not alc2.parse(Message([MessageSegment.at(11454), "chat"])).matched
    assert not alc2.parse(Message([img, "chat"])).matched


def test_v12():
    from nonebot_plugin_alconna.adapters.onebot12 import Mention, Image
    from nonebot.adapters.onebot.v12 import Message, MessageSegment

    msg = Message(["Hello!12", MessageSegment.mention("123")])
    img = MessageSegment.image("1.png")
    print(msg)

    alc = Alconna("Hello!12", Args["target", Mention])
    res = alc.parse(msg)
    assert res.matched
    assert res.target.data['user_id'] == '123'
    assert not alc.parse(Message(["Hello!", img])).matched

    alc1 = Alconna(Image)
    assert alc1.parse(Message([img])).header_match.origin == img

    alc2 = Alconna([MessageSegment.mention('114514')], "chat")
    assert alc2.parse(Message([MessageSegment.mention('114514'), "chat"])).matched
    assert not alc2.parse(Message([MessageSegment.mention('11454'), "chat"])).matched
    assert not alc2.parse(Message([img, "chat"])).matched

    msg1 = Message("Hello! --foo 123")
    print(msg1)

    alc3 = Alconna("Hello!", Option("--foo", Args["foo", int]))
    res1 = alc3.parse(msg1)
    assert res1.matched
    assert res1.query("foo.foo") == 123
    assert not alc3.parse(Message(["Hello!", img])).matched


test_v11()
test_v12()

