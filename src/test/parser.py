from arclet.alconna import Alconna, Args


def test_v11():
    from nonebot_plugin_alconna.adapters.onebot import At, Image
    from nonebot.adapters.onebot.v11 import Message, MessageSegment

    msg = Message(["Hello!", MessageSegment.at(123)])
    print(msg)

    alc = Alconna("Hello!", Args["target", At])
    res = alc.parse(msg)
    assert res.matched
    assert res.target.data['qq'] == '123'

    alc1 = Alconna(Image)
    img = MessageSegment.image(b'123')
    assert alc1.parse(Message([img])).header_match.origin == img


def test_v12():
    from nonebot_plugin_alconna.adapters.onebot import Mention
    from nonebot.adapters.onebot.v12 import Message, MessageSegment

    msg = Message(["Hello!", MessageSegment.mention("123")])
    print(msg)

    alc = Alconna("Hello!", Args["target", Mention])
    res = alc.parse(msg)
    assert res.matched
    assert res.target.data['user_id'] == '123'


test_v11()
test_v12()
