from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot.adapters.satori.bot import Bot as SatoriBot

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.target import Target, TargetFetcher


class SatoriTargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.satori

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, SatoriBot)
        if not target or target.private:
            friends = await bot.friend_list()
            for friend in friends.data:
                yield Target(
                    str(friend.id),
                    private=True,
                    adapter=self.get_adapter(),
                    platform=bot.platform,
                    self_id=bot.self_id,
                )
            while friends.next:
                friends = await bot.friend_list(next_token=friends.next)
                for friend in friends.data:
                    yield Target(
                        str(friend.id),
                        private=True,
                        adapter=self.get_adapter(),
                        platform=bot.platform,
                        self_id=bot.self_id,
                    )
        if not target or not target.private:
            if target and target.parent_id:
                guilds = [await bot.guild_get(guild_id=target.parent_id)]
            else:
                guilds = []
                resp = await bot.guild_list()
                guilds.extend(resp.data)
                while resp.next:
                    resp = await bot.guild_list(next_token=resp.next)
                    guilds.extend(resp.data)
            for guild in guilds:
                channels = await bot.channel_list(guild_id=guild.id)
                for channel in channels.data:
                    yield Target(
                        str(channel.id),
                        str(guild.id),
                        adapter=self.get_adapter(),
                        platform=bot.platform,
                        self_id=bot.self_id,
                        extra={"channel_type": channel.type},
                    )
                while channels.next:
                    channels = await bot.channel_list(guild_id=guild.id, next_token=channels.next)
                    for channel in channels.data:
                        yield Target(
                            str(channel.id),
                            str(guild.id),
                            adapter=self.get_adapter(),
                            platform=bot.platform,
                            self_id=bot.self_id,
                            extra={"channel_type": channel.type},
                        )
