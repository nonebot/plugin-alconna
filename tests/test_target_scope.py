import pytest
from nonebug import App
from nonebot import get_adapter
from nonebot.adapters.qq import Bot as QQBot
from nonebot.adapters.qq import Adapter as QQAdapter
from nonebot.adapters.satori import Bot as SatoriBot
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11 import Bot as Onebot11Bot
from nonebot.adapters.onebot.v12 import Bot as Onebot12Bot
from nonebot.adapters.satori import Adapter as SatoriAdapter
from nonebot.adapters.onebot.v11 import Adapter as Onebot11Adapter
from nonebot.adapters.onebot.v12 import Adapter as Onebot12Adapter


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

        assert Target("0", scope=SupportScope.qq_client).select() in (satori_bot_cc, onebot11_bot, onebot12_bot)
        assert Target("0", scope=SupportScope.qq_api).select() in (satori_bot_qq, qq_bot)

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
