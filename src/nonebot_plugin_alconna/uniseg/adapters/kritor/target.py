from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot.adapters.kritor.bot import Bot as KritorBot

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.target import Target, TargetFetcher


class KritorTargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.kritor

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, KritorBot)
        if not target or not target.private:
            groups = await bot.get_group_list()
            for group in groups:
                yield Target(
                    str(group.group_id),
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
        if not target or target.private:
            friends = await bot.get_friend_list(refresh=True)
            for friend in friends:
                yield Target(
                    str(friend.uin or friend.uid),
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
        if target and target.channel:
            channels = await bot.get_guild_channel_list(guild_id=str(target.parent_id), refresh=True)
            for channel in channels:
                yield Target(
                    str(channel.channel_id),
                    parent_id=str(channel.guild_id),
                    channel=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
