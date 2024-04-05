import pytest
from nonebug import App
from nonebot import get_adapter
from arclet.alconna import Alconna
from nonebot.adapters.onebot.v11.event import Reply
from nonebot.compat import model_dump, type_validate_python
from nonebot.adapters.onebot.v11 import Bot, Adapter, Message, MessageSegment

from tests.fake import fake_group_message_event_v11


def test_uniseg():
    from nonebot_plugin_alconna import Text, Other, Segment
    from nonebot_plugin_alconna.uniseg import FallbackSegment

    assert str(Other(FallbackSegment.text("123"))) == "[text]"
    assert str(Segment()) == "[segment]"
    assert str(Text("123")) == "123"


def test_unimsg():
    from nonebot_plugin_alconna.uniseg import FallbackSegment
    from nonebot_plugin_alconna import Text, Other, Segment, UniMessage

    msg = UniMessage([Other(FallbackSegment.text("123")), Segment(), Text("123")])
    assert str(msg) == "[text][segment]123"
    assert (
        repr(msg)
        == "[Other(origin=FallbackSegment(type='text', data={'text': '123'})), Segment(), Text(text='123', styles={})]"  # noqa: E501
    )
    assert (
        repr(UniMessage.text("123") + Other(FallbackSegment.text("123")))
        == "[Text(text='123', styles={}), Other(origin=FallbackSegment(type='text', data={'text': '123'}))]"
    )


@pytest.mark.asyncio()
async def test_unimsg_template(app: App):
    from nonebot_plugin_alconna.uniseg import FallbackSegment
    from nonebot_plugin_alconna import At, Text, Other, UniMessage, on_alconna

    assert UniMessage.template("{} {}").format("hello", Other(FallbackSegment.text("123"))) == UniMessage(
        [Text("hello "), Other(FallbackSegment.text("123"))]
    )
    assert UniMessage.template("{:At(user, target)}").format(target="123") == UniMessage(At("user", "123"))
    assert UniMessage.template("{:At(flag=user, target=id)}").format(id="123") == UniMessage(At("user", "123"))
    assert UniMessage.template("{:At(flag=user, target=123)}").format() == UniMessage(At("user", "123"))

    matcher = on_alconna(Alconna("test_unimsg_template"))

    @matcher.handle()
    async def handle():
        await matcher.finish(UniMessage.template("{:Reply($message_id)}{:At(user, $event.get_user_id()[1:])}"))

    async with app.test_matcher(matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("test_unimsg_template"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, MessageSegment.reply(1) + MessageSegment.at(23))
        ctx.should_finished(matcher)


@pytest.mark.asyncio()
async def test_uniseg_recv(app: App):
    from nonebot_plugin_alconna import UniMessage
    from nonebot_plugin_alconna import Reply as UniReply

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event2 = fake_group_message_event_v11(
            message_id=2,
            message=Message(
                [
                    MessageSegment.reply(1),
                    MessageSegment.at(123),
                    MessageSegment.text("hello!"),
                ]
            ),
            user_id=789,
            group_id=456,
            reply=type_validate_python(
                Reply,
                model_dump(
                    fake_group_message_event_v11(
                        message_id=1,
                        real_id=1,
                        message=Message("test_uniseg_recv"),
                        user_id=123,
                        group_id=456,
                    )
                ),
            ),
        )
        msg = await UniMessage.generate(event=event2, bot=bot)
        assert msg[UniReply, 0].msg


@pytest.mark.asyncio()
async def test_unimsg_send(app: App):
    from nonebot_plugin_alconna import MsgId, Target, UniMessage, on_alconna

    matcher = on_alconna(Alconna("test_unimsg_send"))

    @matcher.handle()
    async def handle(msg: MsgId):
        receipt = await UniMessage("hello!").send(at_sender=True, reply_to=msg)
        receipt.msg_ids[0] = {"message_id": 2}
        await UniMessage("world!").send(at_sender=True, reply_to=receipt.get_reply())
        assert receipt.recallable
        await receipt.recall(1)

    async with app.test_matcher(matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("test_unimsg_send"), user_id=123, group_id=456)
        ctx.receive_event(bot, event)
        ctx.should_call_api(
            "send_msg",
            {
                "message_type": "group",
                "group_id": 456,
                "message": MessageSegment.reply(1) + MessageSegment.at(123) + MessageSegment.text("hello!"),
            },
        )
        ctx.should_call_api(
            "send_msg",
            {
                "message_type": "group",
                "group_id": 456,
                "message": MessageSegment.reply(2) + MessageSegment.at(123) + MessageSegment.text("world!"),
            },
        )
        ctx.should_call_api("delete_msg", {"message_id": 2})

    async with app.test_api() as ctx1:
        adapter = get_adapter(Adapter)
        _ = ctx1.create_bot(base=Bot, adapter=adapter)
        ctx1.should_call_api(
            "send_msg",
            {
                "message_type": "group",
                "group_id": 456,
                "message": Message("hello!"),
            },
        )
        target = Target("456", adapter=adapter.get_name())
        await target.send("hello!")
