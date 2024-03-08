from arclet.alconna import Args, Alconna


def test_kook():
    from nonebot.adapters.kaiheila.message import Message, MessageSegment

    from nonebot_plugin_alconna.adapters.kook import Mention, KMarkdown

    msg = (
        Message()
        + MessageSegment.text("/command ")
        + MessageSegment.mention("123456")
        + MessageSegment.KMarkdown("12345678")
    )

    alc = Alconna("/command", Args["some_arg", Mention]["some_arg1", KMarkdown])
    ctx = {"$adapter.name": "Kaiheila"}
    res = alc.parse(msg, ctx)
    assert res.matched
    assert res.some_arg.type == "mention"
    assert res.some_arg.data["user_id"] == "123456"
    assert res.some_arg1.data["content"] == "12345678"

    msg1 = Message([MessageSegment.text("/command1 "), MessageSegment.KMarkdown("[(met)123456(met)](42345) 12345678")])

    alc1 = Alconna("/command1", Args["some_arg", str]["some_arg1", str])

    res1 = alc1.parse(msg1, ctx)
    assert res1.matched
    assert res1.some_arg == "[(met)123456(met)](42345)"
    assert res1.some_arg1 == "12345678"
