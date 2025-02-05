from pathlib import Path

import pytest
from nonebug import App
from nonebot import get_adapter
from arclet.alconna import Arparma
from nonebot.adapters.onebot.v11 import Bot, Adapter, Message

from tests.fake import fake_group_message_event_v11

FILE = Path(__file__).parent / "test_koishi_command.yml"
FILE1 = Path(__file__).parent / "test_koishi_command1.yml"


@pytest.mark.asyncio()
async def test_command(app: App):
    from nonebot.matcher import Matcher

    from nonebot_plugin_alconna import Command, command_from_yaml, commands_from_yaml

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

    book1 = command_from_yaml(FILE).build()

    async with app.test_matcher(book1) as ctx:  # type: ignore
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("book1 --anonymous"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "{'writer': (value=Ellipsis args={'id': 1})}")

    books = [cmd.build() for cmd in commands_from_yaml(FILE1).values()]
    for matcher in books:

        @matcher.handle()
        async def _(arp: Arparma, m: Matcher):
            await m.send(str(arp.options))

    async with app.test_matcher(books) as ctx:  # type: ignore
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("book2 --anonymous"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "{'writer': (value=Ellipsis args={'id': 2})}")
        event1 = fake_group_message_event_v11(message=Message("book3 --anonymous"), user_id=123)
        ctx.receive_event(bot, event1)
        ctx.should_call_send(event1, "{'writer': (value=Ellipsis args={'id': 3})}")
