from arclet.alconna import Alconna, Args
from nonebot import get_adapter
from nonebot.adapters.onebot.v11 import Adapter, Bot, Message, MessageSegment
from nonebot.adapters.onebot.v11.event import Reply
from nonebot.compat import model_dump, type_validate_python
from nonebug import App
import pytest

from tests.fake import fake_group_message_event_v11, fake_private_message_event_v11


def ansi(*code) -> str:
    codes = ";".join(str(c) for c in code)
    return f"\033[{codes}m"


def test_uniseg():
    from nonebot_plugin_alconna import Other, Segment, Text, Video, select
    from nonebot_plugin_alconna.uniseg import FallbackSegment

    assert str(Other(FallbackSegment.text("123"))) == "[text]"
    assert str(Segment()) == "[segment]"
    assert str(Text("123")) == "123"

    text = Text("hello world").color("red", 0, -3).italic(3, -2)
    assert text.split() == [Text("hello").color("red").italic(3), Text("world").color("red", 0, -3).italic(0, -2)]
    assert text[3:] == Text("lo world").color("red", 0, -3).italic(0, -2)

    text1 = Text("hello world man").color("red", 0, -3).italic(3, -2)
    assert text1.split() == [
        Text("hello").color("red").italic(3),
        Text("world").color("red").italic(),
        Text("man").italic(0, 1),
    ]
    assert text1.replace("o", "e") == Text("helle werld man").color("red", 0, -3).italic(3, -2)
    assert f"{text1:#}" == f"{ansi(31)}hel{ansi(0)}{ansi(31, 3)}lo world {ansi(0)}{ansi(3)}m{ansi(0)}an"
    pat = select(Text)
    assert pat.first.validate(Text("foobar")).value() == Text("foobar")
    assert pat.first.validate(Video(url="foobar")(Text("foobar"))).value() == Text("foobar")
    assert pat.first.validate(Other(FallbackSegment.text("foobar"))(Text("foobar"))).value() == Text("foobar")
    pat1 = select(Text).from_(Video)
    assert pat1.first.validate(Text("foobar")).failed
    assert pat1.first.validate(Video(url="foobar")(Text("foobar"))).value() == Text("foobar")
    assert pat1.first.validate(Other(FallbackSegment.text("foobar"))(Text("foobar"))).failed

    text2 = (
        Text("[")
        + Text("AAA").color("green")
        + Text(" - ")
        + Text("BB").color("blue")
        + Text("]")
        + Text("\n")
        + Text("@Mr.Lee").color("yellow")
        + Text("test")
    )
    assert str(text2) == "[<green>AAA</green> - <blue>BB</blue>]\n<yellow>@Mr.Lee</yellow>test"


def test_unimsg():
    from nonebot_plugin_alconna import At, Other, Segment, Text, UniMessage
    from nonebot_plugin_alconna.uniseg import FallbackSegment

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

    msg1 = UniMessage.at("123").at_channel("456").at_role("789")
    assert repr(msg1) == (
        "[At(flag='user', target='123', display=None), "
        "At(flag='channel', target='456', display=None), "
        "At(flag='role', target='789', display=None)]"
    )
    assert f"{msg1:*}" == "[at:flag=user,target=123][at:flag=channel,target=456][at:flag=role,target=789]"
    assert msg1.select(At).filter(lambda x: x.flag == "user") == UniMessage.at("123")
    assert msg1.select(At).map(lambda x: x.target) == ["123", "456", "789"]
    assert UniMessage.text("123").at("456").export_sync(adapter="OneBot V11") == MessageSegment.text(
        "123"
    ) + MessageSegment.at("456")
    assert msg1.transform({"at": lambda attrs, _: Text(attrs["target"])}) == UniMessage.text("123456789")

    msg2 = msg1 + Text("abc ")
    assert msg2.lstrip(At) == UniMessage.text("abc ")
    assert msg2.rstrip() == msg1 + Text("abc")

    assert UniMessage.text("123").style("\n", "br").text("456").export_sync(adapter="OneBot V11") == Message("123\n456")


def test_persistence():
    from nonebot_plugin_alconna import Image, UniMessage

    msg = UniMessage.at("123").at_channel("456").image(url="https://example.com/1.jpg").text("hello")
    assert msg.dump() == [
        {"type": "at", "flag": "user", "target": "123"},
        {"type": "at", "flag": "channel", "target": "456"},
        {"type": "image", "url": "https://example.com/1.jpg", "sticker": False},
        {"type": "text", "text": "hello"},
    ]
    assert (
        msg.dump(json=True)
        == """\
[{"type": "at", "flag": "user", "target": "123"}, \
{"type": "at", "flag": "channel", "target": "456"}, \
{"type": "image", "url": "https://example.com/1.jpg", "sticker": false}, \
{"type": "text", "text": "hello"}]"""
    )

    msg1 = [
        {"type": "at", "flag": "user", "target": "456"},
        {"type": "text", "text": "world"},
    ]
    assert UniMessage.load(msg1) == UniMessage.at("456").text("world")

    msg2 = UniMessage.image(raw=b"123", mimetype="image/jpeg")
    assert msg2.dump(media_save_dir=True) == [
        {"type": "image", "raw": "MTIz", "mimetype": "image/jpeg", "sticker": False}
    ]
    assert msg2.dump(media_save_dir=False) == [
        {"type": "image", "raw": b"123", "mimetype": "image/jpeg", "sticker": False}
    ]

    msg3 = [{"type": "image", "raw": "MTIz", "mimetype": "image/jpeg"}]
    assert UniMessage.load(msg3) == msg2

    msg4 = UniMessage(Image(url="https://example.com/1.jpg")(Image(raw=b"123")))
    assert msg4.dump(media_save_dir=True) == [
        {
            "type": "image",
            "url": "https://example.com/1.jpg",
            "sticker": False,
            "children": [{"type": "image", "raw": "MTIz", "sticker": False}],
        },
    ]


@pytest.mark.asyncio()
async def test_fallback(app: App):
    from nonebot.adapters.console import Message

    from nonebot_plugin_alconna.uniseg import Button, SerializeFailed, UniMessage, fallback

    msg = UniMessage.at("123").at_channel("456").image(url="https://example.com/1.jpg").text("hello")
    with pytest.raises(SerializeFailed):
        await msg.export(adapter="OneBot V11", fallback=fallback.FORBID)
    assert (await msg.export(adapter="Console", fallback=fallback.IGNORE)) == Message("hello")
    assert (await msg.export(adapter="Console", fallback=fallback.TO_TEXT)) == Message("[at][at][image]hello")

    msg1 = UniMessage.keyboard(Button("input", "foo", text="/bar"))
    assert (await msg1.export(adapter="Console", fallback=fallback.ROLLBACK)) == Message("foo[/bar]")

    assert (await msg.export(adapter="Console", fallback=fallback.AUTO)) == Message(
        "@123 #456 [image]https://example.com/1.jpg hello"
    )


@pytest.mark.asyncio()
async def test_unimsg_template(app: App):
    from nonebot_plugin_alconna import At, Match, Other, Text, UniMessage, on_alconna
    from nonebot_plugin_alconna.uniseg import FallbackSegment

    assert UniMessage.template("{} {}").format("hello", Other(FallbackSegment.text("123"))) == UniMessage(
        [Text("hello "), Other(FallbackSegment.text("123"))]
    )
    assert UniMessage.template("{:At(user, target)}").format(target="123") == UniMessage(At("user", "123"))
    assert UniMessage.template("{:At(flag=user, target=id)}").format(id="123") == UniMessage(At("user", "123"))
    assert UniMessage.template("{:At(flag=user, target=123)}").format() == UniMessage(At("user", "123"))
    assert UniMessage.template("{foo.target}").format(foo=At("user", "123")) == UniMessage("123")

    matcher = on_alconna(Alconna("test_unimsg_template"))

    @matcher.handle()
    async def _():
        await matcher.finish(UniMessage.template("{:Reply($message_id)}{:At(user, $event.get_user_id()[1:])}"))

    async with app.test_matcher(matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("test_unimsg_template"), user_id=123)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, MessageSegment.reply(event.message_id) + MessageSegment.at(23))
        ctx.should_finished(matcher)

    matcher1 = on_alconna(Alconna("test_unimsg_template1", Args["foo?", str]["bar?", str]))

    @matcher1.handle()
    async def _(foo: Match[str], bar: Match[str]):
        if foo.available:
            matcher1.set_path_arg("foo", foo.result)
        if bar.available:
            matcher1.set_path_arg("bar", bar.result)

    @matcher1.got_path(
        "foo",
        prompt=UniMessage.template("{:At(user, $event.get_user_id())} 请确认目标 foo"),
    )
    @matcher1.got_path(
        "bar",
        prompt=UniMessage.template("{:At(user, $event.get_user_id())} 请确认目标 bar"),
    )
    async def _():
        await matcher1.send(
            UniMessage.template("{:At(user, $event.get_user_id())} 已确认目标为 {foo}, {bar}"),
        )

    async with app.test_matcher(matcher1) as ctx1:
        adapter = get_adapter(Adapter)
        bot = ctx1.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("test_unimsg_template1"), user_id=123)
        ctx1.receive_event(bot, event)
        ctx1.should_call_send(event, MessageSegment.at(123) + " 请确认目标 foo")
        ctx1.should_rejected(matcher1)
        event1 = fake_group_message_event_v11(message=Message("123"), user_id=123)
        ctx1.receive_event(bot, event1)
        ctx1.should_call_send(event1, MessageSegment.at(123) + " 请确认目标 bar")
        ctx1.should_rejected(matcher1)
        event2 = fake_group_message_event_v11(message=Message("456"), user_id=123)
        ctx1.receive_event(bot, event2)
        ctx1.should_call_send(event2, MessageSegment.at(123) + " 已确认目标为 123, 456")


@pytest.mark.asyncio()
async def test_uniseg_recv(app: App):
    from nonebot_plugin_alconna import Reply as UniReply
    from nonebot_plugin_alconna import UniMessage

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event2 = fake_group_message_event_v11(
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
                        real_id=1,
                        message=Message("test_uniseg_recv"),
                        user_id=123,
                        group_id=456,
                    )
                ),
            ),
        )
        msg = await UniMessage.of(message=event2.get_message(), bot=bot).attach_reply(event2, bot)
        assert msg[UniReply, 0].msg


@pytest.mark.asyncio()
async def test_unimsg_send(app: App):
    from nonebot_plugin_alconna import MsgId, Target, UniMessage, on_alconna

    matcher = on_alconna(Alconna("test_unimsg_send"))

    @matcher.handle()
    async def handle(msg: MsgId):
        receipt = await UniMessage("hello!").send(at_sender=True, reply_to=msg)
        receipt.msg_ids[0] = {"message_id": int(msg) + 1}
        await UniMessage("world!").send(at_sender=True, reply_to=receipt.get_reply(0))
        assert receipt.recallable
        await receipt.recall(1)

    async with app.test_matcher(matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        event = fake_group_message_event_v11(message=Message("test_unimsg_send"), user_id=123, group_id=456)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            MessageSegment.reply(event.message_id) + MessageSegment.at(123) + MessageSegment.text("hello!"),
        )
        ctx.should_call_send(
            event,
            MessageSegment.reply(event.message_id + 1) + MessageSegment.at(123) + MessageSegment.text("world!"),
        )
        ctx.should_call_api("delete_msg", {"message_id": event.message_id + 1})
        event1 = fake_private_message_event_v11(message=Message("test_unimsg_send"), user_id=123)
        ctx.receive_event(bot, event1)
        ctx.should_call_send(
            event1,
            MessageSegment.reply(event1.message_id) + MessageSegment.text("hello!"),
        )
        ctx.should_call_send(
            event1,
            MessageSegment.reply(event1.message_id + 1) + MessageSegment.text("world!"),
        )
        ctx.should_call_api("delete_msg", {"message_id": event1.message_id + 1})

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
