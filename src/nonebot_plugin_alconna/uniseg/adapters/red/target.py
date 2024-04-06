from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot.adapters.red.bot import Bot as RedBot

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.target import Target, TargetFetcher


class RedTargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.red

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, RedBot)
        if target and target.channel:
            return
        if not target or not target.private:
            groups = await bot.get_groups()
            for group in groups:
                yield Target(
                    str(group.groupCode),
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
        if not target or target.private:
            friends = await bot.get_friends()
            for friend in friends:
                yield Target(
                    str(friend.uin or friend.uid),
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
