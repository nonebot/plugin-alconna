from arclet.alconna import Args, Alconna


def test_v11():
    from nonebot.adapters.onebot.v11 import Message, MessageSegment

    from nonebot_plugin_alconna import AtID

    msg = Message("Hello!11") + MessageSegment.at(123)
    msg1 = Message("Hello!11 @123")
    msg2 = Message("Hello!11 @abcd")

    ctx = {"$adapter.name": "OneBot V11"}
    alc = Alconna("Hello!11", Args["target", AtID])
    assert alc.parse(msg, ctx).matched
    assert alc.parse(msg1, ctx).matched
    assert alc.parse(msg2, ctx).matched
    assert not alc.parse(Message("Hello!11 123"), ctx).matched
    assert not alc.parse(Message("Hello!11") + MessageSegment.face(123), ctx).matched


def test_v12():
    from nonebot.adapters.onebot.v12 import Message, MessageSegment

    from nonebot_plugin_alconna import AtID

    msg = Message("Hello!12") + MessageSegment.mention("123")
    msg1 = Message("Hello!12 @123")
    msg2 = Message("Hello!12 @abcd")

    ctx = {"$adapter.name": "OneBot V12"}
    alc = Alconna("Hello!12", Args["target", AtID])
    assert alc.parse(msg, ctx).matched
    assert alc.parse(msg1, ctx).matched
    assert alc.parse(msg2, ctx).matched
    assert not alc.parse(Message("Hello!12 123"), ctx).matched
    assert not alc.parse(Message("Hello!12") + MessageSegment.image("1.png"), ctx).matched
