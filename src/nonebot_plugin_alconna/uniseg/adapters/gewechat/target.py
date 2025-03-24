from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot.adapters.gewechat.bot import Bot as GewechatBot

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.target import Target, TargetFetcher


class GeWeChatTargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.gewechat

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, GewechatBot)
        if target and (target.channel or target.parent_id):
            return
        if not target or target.private:
            users = await bot.getPhoneAddressList()
            for info in users.data:
                yield Target(
                    info.userName,
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
