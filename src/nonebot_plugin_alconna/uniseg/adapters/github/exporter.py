from typing import Union

from nonebot.adapters import Bot, Event
from nonebot.adapters.github.event import MessageEvent  # type: ignore
from nonebot.adapters.github.message import Message, MessageSegment  # type: ignore

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.segment import At, Text, Image
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, export


class GithubMessageExporter(MessageExporter["Message"]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.github

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        return Target(
            event.get_user_id(),
            adapter=self.get_adapter(),
            self_id=bot.self_id if bot else None,
            scope=SupportScope.github,
        )

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.id)  # type: ignore

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        return MessageSegment.text(f"@{seg.target}")

    @export
    async def image(self, seg: Image, bot: Bot) -> "MessageSegment":
        if seg.url:
            return MessageSegment.text(f"![]({seg.url})")
        if seg.__class__.to_url and seg.path:
            url = await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name)
            return MessageSegment.text(f"![]({url})")
        if seg.__class__.to_url and seg.raw:
            url = await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name)
            return MessageSegment.text(f"![]({url})")
        raise ValueError("github image segment must have url")

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        raise NotImplementedError
