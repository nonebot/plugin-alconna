from arclet.alconna import Args, Alconna


def test_v11():
    from nonebot.adapters.onebot.v11 import Message

    from nonebot_plugin_alconna import AtID
    from nonebot_plugin_alconna.adapters.onebot11 import At, Face

    msg = Message("Hello!11") + At(123)
    msg1 = Message("Hello!11 @123")
    msg2 = Message("Hello!11 @abcd")

    ctx = {"$adapter.name": "OneBot V11"}
    alc = Alconna("Hello!11", Args["target", AtID])
    assert alc.parse(msg, ctx).matched
    assert alc.parse(msg1, ctx).matched
    assert alc.parse(msg2, ctx).matched
    assert not alc.parse(Message("Hello!11 123"), ctx).matched
    assert not alc.parse(Message("Hello!11") + Face(123), ctx).matched


def test_v12():
    from nonebot.adapters.onebot.v12 import Message

    from nonebot_plugin_alconna import AtID
    from nonebot_plugin_alconna.adapters.onebot12 import Image, Mention

    msg = Message("Hello!12") + Mention("123")
    msg1 = Message("Hello!12 @123")
    msg2 = Message("Hello!12 @abcd")

    ctx = {"$adapter.name": "OneBot V12"}
    alc = Alconna("Hello!12", Args["target", AtID])
    assert alc.parse(msg, ctx).matched
    assert alc.parse(msg1, ctx).matched
    assert alc.parse(msg2, ctx).matched
    assert not alc.parse(Message("Hello!12 123"), ctx).matched
    assert not alc.parse(Message("Hello!12") + Image("1.png"), ctx).matched
