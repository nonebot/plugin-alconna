from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11.bot import Bot as Onebot11Bot

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.target import Target, TargetFetcher


class Onebot11TargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.onebot11

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, Onebot11Bot)
        if target and target.channel:
            return
        if not target or not target.private:
            groups = await bot.get_group_list()
            for group in groups:
                yield Target(
                    str(group["group_id"]),
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
        if not target or target.private:
            friends = await bot.get_friend_list()
            for friend in friends:
                yield Target(
                    str(friend["user_id"]),
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
