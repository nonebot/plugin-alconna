from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot.adapters.mail.bot import Bot as MailBot

from nonebot_plugin_alconna.uniseg.target import Target, TargetFetcher
from nonebot_plugin_alconna.uniseg.constraint import SupportScope, SupportAdapter


class MailTargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.mail

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, MailBot)
        if target and not target.private:
            return
        for uid in await bot.get_unseen_uids():
            yield Target(uid, private=True, adapter=self.get_adapter(), self_id=bot.self_id, scope=SupportScope.mail)
