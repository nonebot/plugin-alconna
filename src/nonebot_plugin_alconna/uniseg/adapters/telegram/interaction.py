from nonebot.adapters import Bot, Event
from nonebot.adapters.telegram import Bot as TelegramBot
from nonebot.adapters.telegram.event import CallbackQueryEvent

from nonebot_plugin_alconna.uniseg.interaction import ButtonInteraction, ButtonInteractionAdapter


class TelegramButtonInteractionAdapter(ButtonInteractionAdapter):
    async def extract_button(self, bot: Bot, event: Event) -> ButtonInteraction | None:
        if not isinstance(bot, TelegramBot) or not isinstance(event, CallbackQueryEvent) or event.data is None:
            return None
        await bot.answer_callback_query(callback_query_id=event.id)
        return ButtonInteraction(bot, event, event.data, event.data, user_id=str(event.from_.id))
