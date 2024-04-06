from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot.adapters.dodo.bot import Bot as DodoBot

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.target import Target, TargetFetcher


class DodoTargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.dodo

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, DodoBot)
        if target and not target.channel:
            return
        if target and target.parent_id:
            islands = [await bot.get_island_info(island_source_id=target.parent_id)]
        else:
            islands = await bot.get_island_list()
        for island in islands:
            channels = await bot.get_channel_list(island_source_id=island.island_source_id)
            for channel in channels:
                yield Target(
                    channel.channel_id,
                    island.island_source_id,
                    channel=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                    extra={"channel_type": channel.channel_type},
                )
