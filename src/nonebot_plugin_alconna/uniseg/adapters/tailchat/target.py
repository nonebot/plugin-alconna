from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot_adapter_tailchat.bot import Bot as TailChatBot

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.target import Target, TargetFetcher


class TailChatTargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.tail_chat

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, TailChatBot)
        if not target or target.private:
            friends = await bot.getAllConverse()
            for friend in friends:
                yield Target(
                    friend,
                    private=True,
                    channel=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
        if not target or not target.private:
            groups = await bot.getUserGroups()
            for group in groups:
                for panel in group.panels:
                    yield Target(
                        panel.id,
                        group.id,
                        channel=True,
                        adapter=self.get_adapter(),
                        self_id=bot.self_id,
                    )
