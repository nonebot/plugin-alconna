import pytest
from nonebug import App
from arclet.alconna import Args, Alconna
from nonebot import on_message, get_adapter
from nonebot.adapters.qq.models import Action
from nonebot.adapters.qq.models import Button as QQButton
from nonebot.adapters.qq import Bot, Adapter, Message, MessageSegment
from nonebot.adapters.qq.models import (
    Permission,
    RenderData,
    InlineKeyboard,
    MessageKeyboard,
    MessageMarkdown,
    InlineKeyboardRow,
    MessageMarkdownParams,
)

from tests.fake import fake_message_event_guild


@pytest.mark.asyncio()
async def test_send(app: App):
    from nonebot_plugin_alconna import At, on_alconna

    def check(name: str):
        if isinstance(name, str):
            return name
        return None

    cmd = on_alconna(Alconna([At], "test", Args["name", check]))

    @cmd.handle()
    async def _():
        await cmd.finish("test!")

    async with app.test_matcher(cmd) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, bot_info=None)
        event = fake_message_event_guild(message=Message("<@5678> test aaaa"))
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "test!")
        ctx.should_finished()

    from nonebot_plugin_alconna import Button
    from nonebot_plugin_alconna.builtins.uniseg.markdown import Markdown

    matcher = on_message()

    @matcher.handle()
    async def _():
        await (
            Markdown(
                template_id="102060544_1720161790",
                params={
                    "text": ["a"],
                    "image_spec": ["#1024px #648px"],
                    "image": ["http://res.dunnoaskrf.top/gacha_sim_910f39dca8bb930cc35175f23289dd65.png"],
                },
            )
            + Button("enter", "再来一发", text="/十连")
        ).send()

    async with app.test_matcher(matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, bot_info=None)
        event = fake_message_event_guild(message=Message("<@5678> test aaaa"))
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            MessageSegment.markdown(
                MessageMarkdown(
                    custom_template_id="102060544_1720161790",
                    params=[
                        MessageMarkdownParams(key="text", values=["a"]),
                        MessageMarkdownParams(key="image_spec", values=["#1024px #648px"]),
                        MessageMarkdownParams(
                            key="image",
                            values=["http://res.dunnoaskrf.top/gacha_sim_910f39dca8bb930cc35175f23289dd65.png"],
                        ),
                    ],
                )
            )
            + MessageSegment.keyboard(
                MessageKeyboard(
                    content=InlineKeyboard(
                        rows=[
                            InlineKeyboardRow(
                                buttons=[
                                    QQButton(
                                        render_data=RenderData(label="再来一发", visited_label="再来一发", style=1),
                                        action=Action(
                                            type=2,
                                            data="/十连",
                                            permission=Permission(type=2),
                                            enter=True,
                                            unsupport_tips="该版本暂不支持查看此消息，请升级至最新版本。",
                                        ),
                                    ),
                                ]
                            )
                        ]
                    )
                )
            ),
        )
        ctx.should_finished()
