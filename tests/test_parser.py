from arclet.alconna import Args, Option, Alconna, store_true


def test_fallback():
    import nonebot_plugin_alconna  # noqa: F401

    assert Alconna("test_fallback").parse("test_fallback").matched


def test_shortcut():
    cchess = Alconna(
        "cchess",
        Option("--battle", default=False, action=store_true, help_text="开始一场对局"),
        Option("--black", default=False, action=store_true, help_text="执黑"),
        Option("-l|--level", Args["level", int], help_text="设置AI等级"),
    )

    def wrapper(slot, content):
        if slot == "mode":
            if content in ("对战", "双人"):
                return "--battle"
            return
        elif slot == "order":
            if content in ("后手", "执黑"):
                return "--black"
            return
        elif slot == "level":
            return f"--level {content or 1}"
        return content

    cchess.shortcut(
        r"象棋(?P<mode>对战|双人|人机|单机)?(?P<order>先手|执白|后手|执黑)?(?:[lL][vV](?P<level>[1-8]))?",
        wrapper=wrapper,
        arguments=["{mode}", "{order}", "{level}"],
    )

    assert cchess.parse("象棋对战执黑lv8").query[int]("level") == 8
    assert cchess.parse("象棋对战先手").query[bool]("battle")
    assert cchess.parse("象棋人机先手").query[int]("level") == 1


def test_v11():
    from nonebot.adapters.onebot.v11 import Message

    from nonebot_plugin_alconna import At as GenericAt
    from nonebot_plugin_alconna.adapters.onebot11 import At, Image

    msg = Message("Hello!11") + At(123)
    img = Image(b"123")
    assert str(msg) == "Hello!11[CQ:at,qq=123]"

    ctx = {"$adapter.name": "OneBot V11"}
    alc = Alconna("Hello!11", Args["target", At])
    res = alc.parse(msg, ctx)
    assert res.matched
    assert res.target.data["qq"] == "123"
    assert not alc.parse(Message("Hello!11") + img, ctx).matched

    alc1 = Alconna(Image)
    assert alc1.parse(Message([img]), ctx).header_match.result == img

    alc2 = Alconna([GenericAt("user", "114514")], "chat")
    assert alc2.parse(Message(At(114514)) + "chat", ctx).matched
    assert not alc2.parse(Message(At(11454)) + "chat", ctx).matched
    assert not alc2.parse(Message(img) + "chat", ctx).matched

    alc3 = Alconna([At], "give")
    assert alc3.parse(At(114514) + "give", ctx).matched
    assert alc3.parse(At(1919810) + "give", ctx).matched
    assert not alc3.parse(img + "give", ctx).matched


def test_v12():
    from nonebot.adapters.onebot.v12 import Message

    from nonebot_plugin_alconna import At as GenericAt
    from nonebot_plugin_alconna.adapters.onebot12 import Image, Mention

    msg = Message("Hello!12") + Mention("123")
    img = Image("1.png")
    assert str(msg) == "Hello!12[mention:user_id=123]"

    ctx = {"$adapter.name": "OneBot V12"}
    alc = Alconna("Hello!12", Args["target", Mention])
    res = alc.parse(msg, ctx)
    assert res.matched
    assert res.target.data["user_id"] == "123"
    assert not alc.parse(Message("Hello!") + img, ctx).matched

    alc1 = Alconna(Image)
    assert alc1.parse(Message([img]), ctx).header_match.result == img

    alc2 = Alconna([GenericAt("user", "114514")], "chat")
    assert alc2.parse(Mention("114514") + "chat", ctx).matched
    assert not alc2.parse(Mention("11454") + "chat", ctx).matched
    assert not alc2.parse(img + "chat", ctx).matched

    msg1 = Message("Hello! --foo 123")
    assert str(msg1) == "Hello! --foo 123"

    alc3 = Alconna("Hello!", Option("--foo", Args["foo", int]))
    res1 = alc3.parse(msg1, ctx)
    assert res1.matched
    assert res1.query("foo.foo") == 123
    assert not alc3.parse("Hello!" + img, ctx).matched

    alc4 = Alconna([Mention], "give")
    assert alc4.parse(Mention("114514") + "give", ctx).matched
    assert alc4.parse(Mention("1919810") + "give", ctx).matched
    assert not alc4.parse(img + "give", ctx).matched


def test_generic():
    from nonebot.adapters.onebot.v11 import Message as Onebot11Message
    from nonebot.adapters.onebot.v12 import Message as Onebot12Message

    from nonebot_plugin_alconna.uniseg import At as GenericAt
    from nonebot_plugin_alconna.adapters.onebot11 import At as Onebot11At
    from nonebot_plugin_alconna.adapters.onebot11 import Image as Onebot11Image
    from nonebot_plugin_alconna.adapters.onebot12 import Image as Onebot12Image
    from nonebot_plugin_alconna.adapters.onebot12 import Mention as Onebot12Mention

    msg11 = Onebot11Message("Hello!") + Onebot11At(123)
    msg12 = Onebot12Message("Hello!") + Onebot12Mention("123")
    img11 = Onebot11Image(b"123")
    img12 = Onebot12Image("1.png")
    assert str(msg11) == "Hello![CQ:at,qq=123]"
    assert str(msg12) == "Hello![mention:user_id=123]"

    alc = Alconna("Hello!", Args["target", GenericAt])

    assert alc.parse(msg11, {"$adapter.name": "OneBot V11"}).matched
    assert alc.parse(msg12, {"$adapter.name": "OneBot V12"}).matched
    assert alc.parse(msg11, {"$adapter.name": "OneBot V11"}).target.target == "123"
    assert alc.parse(msg12, {"$adapter.name": "OneBot V12"}).target.target == "123"
    assert not alc.parse(Onebot11Message("Hello!") + img11, {"$adapter.name": "OneBot V11"}).matched
    assert not alc.parse(Onebot12Message("Hello!") + img12, {"$adapter.name": "OneBot V12"}).matched
