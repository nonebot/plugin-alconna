from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot.adapters.mirai2.bot import Bot as MiraiBot

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.target import Target, TargetFetcher


class Mirai2TargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.mirai_community

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, MiraiBot)
        if target and target.channel:
            return
        if not target or not target.private:
            groups = await bot.group_list()
            for group in groups:
                yield Target(
                    str(group["id"]),
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
        if not target or target.private:
            friends = await bot.friend_list()
            for friend in friends:
                yield Target(
                    str(friend["id"]),
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
