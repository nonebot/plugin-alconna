from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot, Event
from nonebot.adapters.console import Bot as ConsoleBot
from nonebot.adapters.console.event import MessageEvent
from nonebot.adapters.console.message import Message, MessageSegment

from nonebot_plugin_alconna.uniseg.segment import Text, Emoji
from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, export


class ConsoleMessageExporter(MessageExporter[Message]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.console

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        return Target(
            event.get_user_id(),
            adapter=self.get_adapter(),
            self_id=bot.self_id if bot else None,
            scope=SupportScope.console,
        )

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.self_id)

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        styles = seg.extract_most_styles()
        if not styles or styles[0] not in ["markup", "markdown"]:
            return MessageSegment.text(seg.text)
        if styles[0] == "markup":
            _style = styles[1] if len(styles) > 1 else "none"
            return MessageSegment.markup(seg.text, _style)
        if styles[0] == "markdown":
            code_theme = styles[1] if len(styles) > 1 else "monokai"
            return MessageSegment.markdown(seg.text, code_theme)
        return MessageSegment.text(seg.text)

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        return MessageSegment.emoji(seg.name or seg.id)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        assert isinstance(bot, ConsoleBot)
        if TYPE_CHECKING:
            assert isinstance(message, Message)
        if isinstance(target, Event):
            target = self.get_target(target, bot)
        return await bot.send_msg(user_id=target.id, message=message)
