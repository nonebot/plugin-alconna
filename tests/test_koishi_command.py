import pytest
from nonebug import App
from nonebot import get_adapter
from arclet.alconna import Arparma
from nonebot.adapters.onebot.v11 import Bot, Adapter, Message

from tests.fake import fake_group_message_event_v11


@pytest.mark.asyncio()
async def test_command(app: App):
    from nonebot_plugin_alconna import Command

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
        await book.send(str(arp.options))

    async with app.test_matcher(book) as ctx:  # type: ignore
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("book --anonymous"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "{'writer': (value=Ellipsis args={'id': 0})}")
