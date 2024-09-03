import pytest
from nonebug import App
from nonebot import get_adapter
from nonebot.adapters.satori import Bot, Adapter, Message, MessageSegment

from tests.fake import FAKE_SATORI_LOGIN, fake_message_event_satori


@pytest.mark.asyncio()
async def test_echo(app: App):
    from nonebot_plugin_alconna import load_builtin_plugin

    load_builtin_plugin("echo")

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, login=FAKE_SATORI_LOGIN, info=None)
        msg = "/echo" + MessageSegment.image(raw=b"123", mime="image/png")
        event = fake_message_event_satori(message=msg, id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, Message('<img src="data:image/png;base64,MTIz"/>'))

        msg1 = Message("/ec<b>hos<i>ome</i>_arg</b>")
        event1 = fake_message_event_satori(message=msg1, id=124)
        ctx.receive_event(bot, event1)
        ctx.should_call_send(event1, Message("<b>s<i>ome</i>_arg</b>"))


@pytest.mark.asyncio()
async def test_help(app: App):
    from nonebot_plugin_alconna import Command, load_builtin_plugin

    # 使用 pdm run test 的时候要把这个注释掉
    # load_builtin_plugin("echo")
    load_builtin_plugin("help")

    test_cmd = Command("test", "test").build()

    @test_cmd.handle()
    async def tt_h():
        await test_cmd.send("ok")

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, login=FAKE_SATORI_LOGIN, info=None)
        msg = Message("/help")
        event = fake_message_event_satori(message=msg, id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            """\
# 当前可用的命令有:
 【0】/echo : echo 指令
 【1】/help : 显示所有命令帮助
 【2】test : test
# 输入'命令名 -h|--help' 查看特定命令的语法""",
        )

        msg1 = Message("/help tes")
        event1 = fake_message_event_satori(message=msg1, id=124)
        ctx.receive_event(bot, event1)
        ctx.should_call_send(
            event1,
            """\
【2】test : test
# 输入'命令名 -h|--help' 查看特定命令的语法""",
        )

        msg2 = Message("/help 2")
        event2 = fake_message_event_satori(message=msg2, id=125)
        ctx.receive_event(bot, event2)
        ctx.should_call_send(event2, Message("test \ntest"))


@pytest.mark.asyncio()
async def test_lang_switch(app: App):
    from tarina.lang import lang

    from nonebot_plugin_alconna import load_builtin_plugin

    load_builtin_plugin("lang")

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, login=FAKE_SATORI_LOGIN, info=None)
        event1 = fake_message_event_satori(message=Message("/lang switch zh-CN"), id=123)
        ctx.receive_event(bot, event1)
        ctx.should_call_send(event1, Message("切换语言成功: 'zh-CN'。"))
        ctx.should_finished()
        assert lang.current == "zh-CN"


# @pytest.mark.asyncio()
# async def test_lang_list_success(app: App):
#     from tarina.lang import _LangConfigData, lang

#     from nonebot_plugin_alconna import load_builtin_plugin

#     load_builtin_plugin("lang")

#     lang.__dict__["_LangConfig__configs"]["test-lang"] = _LangConfigData(
#         default="zh-CN", frozen={}, require={}, name=None, locales={"zh-CN"}
#     )

#     async with app.test_matcher() as ctx:
#         adapter = get_adapter(Adapter)
#         bot = ctx.create_bot(base=Bot, adapter=adapter, login=FAKE_SATORI_LOGIN, info=None)
#         lang.select("zh-CN")
#         event = fake_message_event_satori(message=Message("/lang list test-lang"), id=123)
#         ctx.receive_event(bot, event)
#         ctx.should_call_send(
#             event,
#             Message("""\
# 支持的语言列表:
#  * zh-CN"""),
#         )
#         ctx.should_finished()


@pytest.mark.asyncio()
async def test_lang_list_failure(app: App):
    from tarina.lang import lang

    from nonebot_plugin_alconna import load_builtin_plugin

    load_builtin_plugin("lang")

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, login=FAKE_SATORI_LOGIN, info=None)
        lang.select("zh-CN")
        event = fake_message_event_satori(message=Message("/lang list 404"), id="123")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, Message((MessageSegment.at("1"), MessageSegment.text(" 未能找到 404 所属的 i18n 目录")))
        )
        ctx.should_finished()
