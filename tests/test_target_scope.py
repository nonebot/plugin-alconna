import asyncio

import pytest
from nonebug import App
from pytest_mock import MockerFixture
from nonebot import get_driver, get_adapter
from nonebot.adapters.qq import Bot as QQBot
from nonebot.adapters.qq import Adapter as QQAdapter
from nonebot.adapters.satori import Bot as SatoriBot
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11 import Bot as Onebot11Bot
from nonebot.adapters.onebot.v12 import Bot as Onebot12Bot
from nonebot.adapters.satori import Adapter as SatoriAdapter
from nonebot.adapters.onebot.v11 import Adapter as Onebot11Adapter
from nonebot.adapters.onebot.v12 import Adapter as Onebot12Adapter
from nonebot.adapters.satori.models import User, Guild, Channel, PageResult, ChannelType


@pytest.mark.asyncio()
async def test_bots(app: App):
    from nonebot_plugin_alconna import Target, UniMessage, SupportScope

    async with app.test_api() as ctx:
        qq_adapter = get_adapter(QQAdapter)
        qq_bot = ctx.create_bot(base=QQBot, adapter=qq_adapter, self_id="1", bot_info=None)
        satori_adapter = get_adapter(SatoriAdapter)
        satori_bot_cc = ctx.create_bot(
            base=SatoriBot, adapter=satori_adapter, self_id="2", platform="chronocat", info=None
        )
        satori_bot_qq = ctx.create_bot(base=SatoriBot, adapter=satori_adapter, self_id="3", platform="qq", info=None)
        onebot11_adapter = get_adapter(Onebot11Adapter)
        onebot11_bot = ctx.create_bot(base=Onebot11Bot, adapter=onebot11_adapter, self_id="4")
        onebot12_adapter = get_adapter(Onebot12Adapter)
        onebot12_bot = ctx.create_bot(
            base=Onebot12Bot, adapter=onebot12_adapter, self_id="5", platform="qq", impl="mock"
        )

        assert await Target("0", scope=SupportScope.qq_client).select() in (satori_bot_cc, onebot11_bot, onebot12_bot)
        assert await Target("0", scope=SupportScope.qq_api).select() in (satori_bot_qq, qq_bot)

        target1 = Target("123", adapter=Onebot11Adapter)
        target2 = Target.group("456", scope=SupportScope.qq_client, platform="chronocat")
        target3 = Target.channel_("789", scope=SupportScope.qq_api, adapter=QQAdapter)
        ctx.should_call_api(
            "send_msg",
            {"message_type": "group", "group_id": 123, "message": [MessageSegment(type="text", data={"text": "test"})]},
        )
        await target1.send(UniMessage("test"))
        ctx.should_call_api(
            "message_create",
            {
                "channel_id": "456",
                "content": "test",
            },
        )
        await target2.send(UniMessage("test"))
        ctx.should_call_api("post_messages", {"channel_id": "789", "msg_id": "", "event_id": None, "content": "test"})
        await target3.send(UniMessage("test"))


@pytest.mark.asyncio()
async def test_enable(app: App, mocker: MockerFixture):
    from nonebot_plugin_alconna import Target, apply_fetch_targets

    # 结束后会自动恢复到原来的状态
    mocker.patch("nonebot_plugin_alconna.uniseg._enable_fetch_targets", False)

    apply_fetch_targets()

    async with app.test_api() as ctx:
        satori_adapter = get_adapter(SatoriAdapter)
        satori_bot1 = ctx.create_bot(
            base=SatoriBot, adapter=satori_adapter, self_id="1", platform="chronocat", info=None
        )

        ctx.should_call_api("friend_list", {}, PageResult(data=[User(id="11", name="test1")]))

        ctx.should_call_api("guild_list", {}, PageResult(data=[Guild(id="12", name="test2")]))
        ctx.should_call_api(
            "channel_list", {"guild_id": "12"}, PageResult(data=[Channel(id="13", type=ChannelType.TEXT)])
        )
        await asyncio.sleep(0.1)
        satori_bot2 = ctx.create_bot(
            base=SatoriBot, adapter=satori_adapter, self_id="2", platform="chronocat", info=None
        )
        ctx.should_call_api("friend_list", {}, PageResult(data=[User(id="21", name="test1")]))

        ctx.should_call_api(
            "guild_list", {}, PageResult(data=[Guild(id="12", name="test2"), Guild(id="22", name="test2")])
        )
        ctx.should_call_api(
            "channel_list", {"guild_id": "12"}, PageResult(data=[Channel(id="13", type=ChannelType.TEXT)])
        )
        ctx.should_call_api(
            "channel_list", {"guild_id": "22"}, PageResult(data=[Channel(id="23", type=ChannelType.TEXT)])
        )
        await asyncio.sleep(0.1)
        target1 = Target("11", private=True)
        assert await target1.select() is satori_bot1
        target2 = Target("21", private=True)
        assert await target2.select() is satori_bot2
        target3 = Target("23", parent_id="22")
        assert await target3.select() is satori_bot2
        target4 = Target("13")
        assert await target4.select() in (satori_bot1, satori_bot2)

        with pytest.raises(IndexError):
            await Target("11", adapter=QQAdapter).select()

    # 清理
    driver = get_driver()
    driver._bot_connection_hook.clear()
    driver._bot_disconnection_hook.clear()
