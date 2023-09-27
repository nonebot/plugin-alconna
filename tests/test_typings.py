from arclet.alconna import Args, Alconna


def test_v11():
    from nonebot.adapters.onebot.v11 import Message

    from nonebot_plugin_alconna.adapters.onebot11 import At, AtID, Face

    msg = Message(["Hello!11", At(123)])
    msg1 = Message("Hello!11 @123")
    msg2 = Message("Hello!11 123")

    alc = Alconna("Hello!11", Args["target", AtID])
    assert alc.parse(msg).matched
    assert alc.parse(msg1).matched
    assert alc.parse(msg2).matched
    assert not alc.parse(Message("Hello!11 @abcd")).matched
    assert not alc.parse(Message(["Hello!11", Face(123)])).matched


def test_v12():
    from nonebot.adapters.onebot.v12 import Message

    from nonebot_plugin_alconna.adapters.onebot12 import Image, Mention, MentionID

    msg = Message(["Hello!12", Mention("123")])
    msg1 = Message("Hello!12 @123")
    msg2 = Message("Hello!12 123")

    alc = Alconna("Hello!12", Args["target", MentionID])
    assert alc.parse(msg).matched
    assert alc.parse(msg1).matched
    assert alc.parse(msg2).matched
    assert not alc.parse(Message("Hello!12 @abcd")).matched
    assert not alc.parse(Message(["Hello!12", Image("1.png")])).matched
