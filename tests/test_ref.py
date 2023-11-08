import pytest
from nonebug import App
from nonebot import get_adapter
from arclet.alconna import Arparma
from nonebot.adapters.onebot.v11 import Bot, Adapter, Message

from tests.fake import fake_group_message_event_v11


@pytest.mark.asyncio()
async def test_ref(app: App):
    from nonebot_plugin_alconna import Command, referent

    book = (
        Command("book", "测试")
        .option("writer", "-w <id:int>")
        .option("writer", "--anonymous", {"id": 0})
        .usage("book [-w <id:int> | --anonymous]")
        .shortcut("测试", {"args": ["--anonymous"]})
        .build()
    )

    @book.handle()
    async def _(arp: Arparma):
        await book.send(f"0: {(arp.options)}")

    async with app.test_matcher(book) as ctx:  # type: ignore
        adapter: Adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("book --anonymous"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "0: {'writer': (value=Ellipsis args={'id': 0})}")

    book1 = referent("book")
    assert book1 is book

    @book1.handle(override=("replace", 0))
    async def _(arp: Arparma):
        await book1.send(f"1: {(arp.options)}")

    @book1.handle(override=("insert", 0))
    async def _(arp: Arparma):
        await book1.send(f"2: {(arp.options)}")

    async with app.test_matcher(book) as ctx:  # type: ignore
        adapter: Adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("book --anonymous"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "2: {'writer': (value=Ellipsis args={'id': 0})}")
        ctx.should_call_send(event, "1: {'writer': (value=Ellipsis args={'id': 0})}")
