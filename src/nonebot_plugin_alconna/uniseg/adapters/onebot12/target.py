from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot.adapters.onebot.v12.bot import Bot as Onebot12Bot

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.target import Target, TargetFetcher


class Onebot12TargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.onebot12

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, Onebot12Bot)
        if not target or (not target.private and not target.channel):
            groups = await bot.get_group_list()
            for group in groups:
                yield Target(
                    str(group["group_id"]),
                    adapter=self.get_adapter(),
                    platform=bot.platform,
                    self_id=bot.self_id,
                )
        if not target or target.private:
            friends = await bot.get_friend_list()
            for friend in friends:
                yield Target(
                    str(friend["user_id"]),
                    private=True,
                    adapter=self.get_adapter(),
                    platform=bot.platform,
                    self_id=bot.self_id,
                )
        if not target or target.channel:
            guilds = await bot.get_guild_list()
            for guild in guilds:
                channels = await bot.get_channel_list(guild_id=guild["guild_id"])
                for channel in channels:
                    yield Target(
                        str(channel["channel_id"]),
                        str(guild["guild_id"]),
                        channel=True,
                        adapter=self.get_adapter(),
                        platform=bot.platform,
                        self_id=bot.self_id,
                    )
