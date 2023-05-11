from nonebot_plugin_alconna.rule import AlconnaRule
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from inspect import iscoroutinefunction
from arclet.alconna import Alconna
import asyncio


def t2i(text: str, *args) -> bytes:
    return text.encode()


def send_handler(_: str, text: str):
    data = t2i(text)
    print(_)
    return Message(MessageSegment.image(data))


AlconnaRule.default_converter = send_handler


async def main():
    rule = AlconnaRule(Alconna("1"))
    print(rule.output_converter)
    print(iscoroutinefunction(rule.output_converter))
    print(await rule.output_converter("help", rule.command.get_help()))


asyncio.run(main())
