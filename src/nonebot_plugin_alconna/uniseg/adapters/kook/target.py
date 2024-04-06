from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot.adapters.kaiheila.bot import Bot as KookBot

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.target import Target, TargetFetcher


class KookTargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.kook

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, KookBot)
        if target and not target.channel:
            return
        if target and target.parent_id:
            guilds = [await bot.guild_view(guild_id=target.parent_id)]
        else:
            guilds = []
            resp = await bot.guild_list()
            if resp.guilds:
                guilds.extend(resp.guilds)
            while resp.meta and resp.meta.page != resp.meta.page_total:
                resp = await bot.guild_list(page=(resp.meta.page or 0) + 1)
                if resp.guilds:
                    guilds.extend(resp.guilds)
        for guild in guilds:
            resp1 = await bot.channel_list(guild_id=guild.id_)  # type: ignore
            for channel in resp1.channels or []:
                yield Target(
                    str(channel.id_),
                    str(guild.id_),
                    channel=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                    extra={"channel_type": channel.type},
                )
            while resp1.meta and resp1.meta.page != resp1.meta.page_total:
                resp1 = await bot.channel_list(guild_id=guild.id_, page=resp1.meta.page + 1)  # type: ignore
                for channel in resp1.channels or []:
                    yield Target(
                        str(channel.id_),
                        str(guild.id_),
                        channel=True,
                        adapter=self.get_adapter(),
                        self_id=bot.self_id,
                        extra={"channel_type": channel.type},
                    )
        if not target or target.private:
            resp2 = await bot.userChat_list()
            for chat in resp2.user_chats or []:
                assert chat.target_info
                yield Target(
                    str(chat.target_info.id_),
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
            while resp2.meta and resp2.meta.page != resp2.meta.page_total:
                resp2 = await bot.userChat_list(page=resp2.meta.page + 1)  # type: ignore
                for chat in resp2.user_chats or []:
                    assert chat.target_info
                    yield Target(
                        str(chat.target_info.id_),
                        adapter=self.get_adapter(),
                        self_id=bot.self_id,
                    )
