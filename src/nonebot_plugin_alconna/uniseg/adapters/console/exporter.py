from typing import TYPE_CHECKING, Any, Union, Sequence

from nonechat.model import DIRECT
from nonebot.adapters import Bot, Event
from nonebot.adapters.console import Bot as ConsoleBot
from nonebot.adapters.console.message import Message, MessageSegment
from nonebot.adapters.console.event import MessageEvent, MessageResponse

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.segment import Text, Emoji, Segment
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, export


class ConsoleMessageExporter(MessageExporter[Message]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.console

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        assert isinstance(event, MessageEvent)
        if event.channel.id == DIRECT.id or event.channel.id.startswith("private:"):
            # If the event is a direct message, we can use the user ID as the target ID
            return Target(
                event.user.id,
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.console,
            )
        return Target(
            event.channel.id,
            adapter=self.get_adapter(),
            self_id=bot.self_id if bot else None,
            scope=SupportScope.console,
        )

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return event.message_id

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
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
    async def emoji(self, seg: Emoji, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.emoji(seg.name or seg.id)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, ConsoleBot)
        if TYPE_CHECKING:
            assert isinstance(message, Message)
        if isinstance(target, Event):
            return await bot.send(target, message, **kwargs)  # type: ignore
        if target.private:
            return await bot.send_private_message(user_id=target.id, message=message)
        return await bot.send_message(channel_id=target.id, message=message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, ConsoleBot)
        if isinstance(mid, str):
            if isinstance(context, Event):
                assert isinstance(context, MessageEvent)
                await bot.recall_message(message_id=mid, channel_id=context.channel.id)
            else:
                if context.private:
                    channel_id = (await bot.create_dm(context.id)).id
                else:
                    channel_id = context.id
                await bot.recall_message(message_id=mid, channel_id=channel_id)
        elif isinstance(mid, MessageResponse):
            await bot.recall_message(mid.message_id, channel_id=mid.channel_id)

    async def edit(self, new: Sequence[Segment], mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, ConsoleBot)
        new_msg = await self.export(new, bot, True)
        if isinstance(mid, str):
            if isinstance(context, Event):
                assert isinstance(context, MessageEvent)
                await bot.edit_message(message_id=mid, channel_id=context.channel.id, content=new_msg)
            else:
                if context.private:
                    channel_id = (await bot.create_dm(context.id)).id
                else:
                    channel_id = context.id
                await bot.edit_message(message_id=mid, channel_id=channel_id, content=new_msg)
        elif isinstance(mid, MessageResponse):
            await bot.edit_message(mid.message_id, mid.channel_id, new_msg)
