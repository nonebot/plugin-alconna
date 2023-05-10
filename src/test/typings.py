from arclet.alconna import Alconna, Args


def test_v11():
    from nonebot_plugin_alconna.adapters.onebot11 import AtID, At, Face
    from nonebot.adapters.onebot.v11 import Message

    msg = Message(["Hello!11", At(123)])
    msg1 = Message("Hello!11 @123")
    msg2 = Message("Hello!11 123")
    print(msg)
    print(msg1)
    print(msg2)

    alc = Alconna("Hello!11", Args["target", AtID])
    assert alc.parse(msg).matched
    assert alc.parse(msg1).matched
    assert alc.parse(msg2).matched
    assert not alc.parse(Message("Hello!11 @abcd")).matched
    assert not alc.parse(Message(["Hello!11", Face(123)])).matched


def test_v12():
    from nonebot_plugin_alconna.adapters.onebot12 import MentionID, Image, Mention
    from nonebot.adapters.onebot.v12 import Message

    msg = Message(["Hello!12", Mention('123')])
    msg1 = Message("Hello!12 @123")
    msg2 = Message("Hello!12 123")
    print(msg)
    print(msg1)
    print(msg2)

    alc = Alconna("Hello!12", Args["target", MentionID])
    assert alc.parse(msg).matched
    assert alc.parse(msg1).matched
    assert alc.parse(msg2).matched
    assert not alc.parse(Message("Hello!12 @abcd")).matched
    assert not alc.parse(Message(["Hello!12", Image('1.png')])).matched


test_v11()
test_v12()
