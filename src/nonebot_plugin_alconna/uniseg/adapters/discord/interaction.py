from nonebot.adapters import Bot, Event
from nonebot.adapters.discord.api.model import InteractionResponse
from nonebot.adapters.discord.api.types import ComponentType, InteractionCallbackType
from nonebot.adapters.discord.bot import Bot as DiscordBot
from nonebot.adapters.discord.event import MessageComponentInteractionEvent

from nonebot_plugin_alconna.uniseg.interaction import ButtonInteraction, ButtonInteractionAdapter


class DiscordButtonInteractionAdapter(ButtonInteractionAdapter):
    async def extract_button(self, bot: Bot, event: Event) -> ButtonInteraction | None:
        if (
            not isinstance(bot, DiscordBot)
            or not isinstance(event, MessageComponentInteractionEvent)
            or event.data.component_type != ComponentType.Button
        ):
            return None

        await bot.create_interaction_response(
            interaction_id=event.id,
            interaction_token=event.token,
            response=InteractionResponse(type=InteractionCallbackType.DEFERRED_UPDATE_MESSAGE),
        )
        return ButtonInteraction(bot, event, event.data.custom_id, user_id=event.get_user_id())
