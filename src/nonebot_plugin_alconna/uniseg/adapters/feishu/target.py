from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot.adapters.feishu.bot import Bot as FeishuBot

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.target import Target, TargetFetcher


class FeishuTargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.feishu

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, FeishuBot)
        if target and target.channel:
            return
        if not target or not target.private:
            result = await bot.call_api("im/v1/chats", method="GET")
            for chat in result["data"]["items"]:
                yield Target(
                    chat["chat_id"],
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
            while result["data"]["has_more"]:
                result = await bot.call_api(
                    "im/v1/chats", method="GET", params={"page_token": result["data"]["page_token"]}
                )
                for chat in result["data"]["items"]:
                    yield Target(
                        chat["chat_id"],
                        adapter=self.get_adapter(),
                        self_id=bot.self_id,
                    )
        if target and target.private and target.parent_id:
            params = {"department_id": target.parent_id}
            result = await bot.call_api("contact/v3/users/find_by_department", method="GET")
            for user in result["data"]["items"]:
                yield Target(
                    user["open_id"],
                    target.parent_id,
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
            while result["data"]["has_more"]:
                params["page_token"] = result["data"]["page_token"]
                result = await bot.call_api("contact/v3/users/find_by_department", method="GET", params=params)
                for user in result["data"]["items"]:
                    yield Target(
                        user["open_id"],
                        target.parent_id,
                        private=True,
                        adapter=self.get_adapter(),
                        self_id=bot.self_id,
                    )
        groups = []
        result = await bot.call_api("contact/v3/group/simplelist", method="GET")
        for group in result["data"]["grouplist"]:
            groups.append(group["id"])
        while result["data"]["has_more"]:
            result = await bot.call_api(
                "contact/v3/group/simplelist", method="GET", params={"page_token": result["data"]["page_token"]}
            )
            for group in result["data"]["grouplist"]:
                groups.append(group["id"])
        for group_id in groups:
            result = await bot.call_api(f"contact/v3/group/{group_id}/member/simplelist", method="GET")
            for user in result["data"]["memberlist"]:
                yield Target(
                    user["member_id"],
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
            while result["data"]["has_more"]:
                result = await bot.call_api(
                    f"contact/v3/group/{group_id}/member/simplelist",
                    method="GET",
                    params={"page_token": result["data"]["page_token"]},
                )
                for user in result["data"]["memberlist"]:
                    yield Target(
                        user["member_id"],
                        private=True,
                        adapter=self.get_adapter(),
                        self_id=bot.self_id,
                    )
