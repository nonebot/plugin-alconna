from nonebot_plugin_alconna.rule import AlconnaRule
from nonebot_plugin_alconna import Alconna
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from inspect import iscoroutinefunction
import asyncio


def t2i(text: str, *args) -> bytes:
    return text.encode()


def send_handler(text: str):
    data = t2i(text)
    return Message(MessageSegment.image(data))


AlconnaRule.default_converter = send_handler


async def main():
    rule = AlconnaRule(Alconna("1"))
    print(rule.output_converter)
    print(iscoroutinefunction(rule.output_converter))
    print(await rule.output_converter(rule.command.get_help()))


asyncio.run(main())
