from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot.adapters.discord.api.types import ChannelType
from nonebot.adapters.discord.bot import Bot as DiscordBot

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.target import Target, TargetFetcher


class DiscordTargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.discord

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, DiscordBot)
        if target and not target.channel:
            return
        if target and target.parent_id:
            guilds = [await bot.get_guild(guild_id=int(target.parent_id))]
        else:
            guilds = await bot.get_current_user_guilds()
        for guild in guilds:
            channels = await bot.get_guild_channels(guild_id=guild.id)
            for channel in channels:
                yield Target(
                    str(channel.id),
                    str(guild.id),
                    channel=True,
                    private=channel.type == ChannelType.DM,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                    extra={"channel_type": channel.type},
                )
