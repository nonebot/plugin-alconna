from nonebot.adapters import Bot, Event
from nonebot.adapters.qq.bot import Bot as QQBot
from nonebot.adapters.qq.event import InteractionCreateEvent

from nonebot_plugin_alconna.uniseg.interaction import ButtonInteraction, ButtonInteractionAdapter


class QQButtonInteractionAdapter(ButtonInteractionAdapter):
    async def extract_button(self, bot: Bot, event: Event) -> ButtonInteraction | None:
        if not isinstance(bot, QQBot) or not isinstance(event, InteractionCreateEvent) or event.type != 11:
            return None

        await bot.put_interaction(interaction_id=event.id, code=0)

        resolved = event.data.resolved
        return ButtonInteraction(bot, event, resolved.button_id, resolved.button_data, user_id=event.get_user_id())
