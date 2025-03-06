import pytest
from nonebug import App
from nonebot import get_adapter


@pytest.mark.asyncio()
async def test_button(app: App):
    from nonebot_plugin_alconna import Button, Command, UniMessage

    matcher = Command("test <row:int>").build()

    @matcher.handle()
    async def _(row: int):
        await UniMessage.keyboard(
            Button("action", "1"),
            Button("action", "2"),
            Button("action", "3"),
            Button("action", "4"),
            Button("action", "5"),
            Button("action", "6"),
            Button("action", "7"),
            Button("action", "8"),
            Button("action", "9"),
            row=row,
        ).send()

    async with app.test_matcher(matcher) as ctx:
        from nonebot.adapters.discord.api import Button as DCButton
        from nonebot.adapters.discord.api import ActionRow, ButtonStyle
        from nonebot.adapters.discord import Bot, Adapter, MessageSegment

        from tests.fake import fake_message_event_discord

        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, bot_info=None, self_id="12345", auto_connect=False)
        event = fake_message_event_discord("test 3")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            MessageSegment.component(
                ActionRow(
                    components=[
                        DCButton(style=ButtonStyle.Primary, label="1", custom_id="1"),
                        DCButton(style=ButtonStyle.Primary, label="2", custom_id="2"),
                        DCButton(style=ButtonStyle.Primary, label="3", custom_id="3"),
                    ]
                ),
            )
            + MessageSegment.component(
                ActionRow(
                    components=[
                        DCButton(style=ButtonStyle.Primary, label="4", custom_id="4"),
                        DCButton(style=ButtonStyle.Primary, label="5", custom_id="5"),
                        DCButton(style=ButtonStyle.Primary, label="6", custom_id="6"),
                    ]
                ),
            )
            + MessageSegment.component(
                ActionRow(
                    components=[
                        DCButton(style=ButtonStyle.Primary, label="7", custom_id="7"),
                        DCButton(style=ButtonStyle.Primary, label="8", custom_id="8"),
                        DCButton(style=ButtonStyle.Primary, label="9", custom_id="9"),
                    ]
                ),
            ),
        )
        event1 = fake_message_event_discord("test 4")
        ctx.receive_event(bot, event1)
        ctx.should_call_send(
            event1,
            MessageSegment.component(
                ActionRow(
                    components=[
                        DCButton(style=ButtonStyle.Primary, label="1", custom_id="1"),
                        DCButton(style=ButtonStyle.Primary, label="2", custom_id="2"),
                        DCButton(style=ButtonStyle.Primary, label="3", custom_id="3"),
                        DCButton(style=ButtonStyle.Primary, label="4", custom_id="4"),
                    ]
                ),
            )
            + MessageSegment.component(
                ActionRow(
                    components=[
                        DCButton(style=ButtonStyle.Primary, label="5", custom_id="5"),
                        DCButton(style=ButtonStyle.Primary, label="6", custom_id="6"),
                        DCButton(style=ButtonStyle.Primary, label="7", custom_id="7"),
                        DCButton(style=ButtonStyle.Primary, label="8", custom_id="8"),
                    ]
                ),
            )
            + MessageSegment.component(
                ActionRow(components=[DCButton(style=ButtonStyle.Primary, label="9", custom_id="9")]),
            ),
        )

    async with app.test_matcher(matcher) as ctx:
        from nonebot.adapters.qq.models import Action
        from nonebot.adapters.qq.models import Button as QQButton
        from nonebot.adapters.qq import Bot, Adapter, Message, MessageSegment
        from nonebot.adapters.qq.models import (
            Permission,
            RenderData,
            InlineKeyboard,
            MessageKeyboard,
            InlineKeyboardRow,
        )

        from tests.fake import fake_message_event_guild

        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, bot_info=None)
        event = fake_message_event_guild(message=Message("test 3"))
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            Message(
                MessageSegment.keyboard(
                    MessageKeyboard(
                        content=InlineKeyboard(
                            rows=[
                                InlineKeyboardRow(
                                    buttons=[
                                        QQButton(
                                            id="1",
                                            render_data=RenderData(label="1", visited_label="1", style=1),
                                            action=Action(
                                                type=1,
                                                permission=Permission(type=2),
                                                unsupport_tips="该版本暂不支持查看此消息，请升级至最新版本。",
                                            ),
                                        ),
                                        QQButton(
                                            id="2",
                                            render_data=RenderData(label="2", visited_label="2", style=1),
                                            action=Action(
                                                type=1,
                                                permission=Permission(type=2),
                                                unsupport_tips="该版本暂不支持查看此消息，请升级至最新版本。",
                                            ),
                                        ),
                                        QQButton(
                                            id="3",
                                            render_data=RenderData(label="3", visited_label="3", style=1),
                                            action=Action(
                                                type=1,
                                                permission=Permission(type=2),
                                                unsupport_tips="该版本暂不支持查看此消息，请升级至最新版本。",
                                            ),
                                        ),
                                    ]
                                ),
                                InlineKeyboardRow(
                                    buttons=[
                                        QQButton(
                                            id="4",
                                            render_data=RenderData(label="4", visited_label="4", style=1),
                                            action=Action(
                                                type=1,
                                                permission=Permission(type=2),
                                                unsupport_tips="该版本暂不支持查看此消息，请升级至最新版本。",
                                            ),
                                        ),
                                        QQButton(
                                            id="5",
                                            render_data=RenderData(label="5", visited_label="5", style=1),
                                            action=Action(
                                                type=1,
                                                permission=Permission(type=2),
                                                unsupport_tips="该版本暂不支持查看此消息，请升级至最新版本。",
                                            ),
                                        ),
                                        QQButton(
                                            id="6",
                                            render_data=RenderData(label="6", visited_label="6", style=1),
                                            action=Action(
                                                type=1,
                                                permission=Permission(type=2),
                                                unsupport_tips="该版本暂不支持查看此消息，请升级至最新版本。",
                                            ),
                                        ),
                                    ]
                                ),
                                InlineKeyboardRow(
                                    buttons=[
                                        QQButton(
                                            id="7",
                                            render_data=RenderData(label="7", visited_label="7", style=1),
                                            action=Action(
                                                type=1,
                                                permission=Permission(type=2),
                                                unsupport_tips="该版本暂不支持查看此消息，请升级至最新版本。",
                                            ),
                                        ),
                                        QQButton(
                                            id="8",
                                            render_data=RenderData(label="8", visited_label="8", style=1),
                                            action=Action(
                                                type=1,
                                                permission=Permission(type=2),
                                                unsupport_tips="该版本暂不支持查看此消息，请升级至最新版本。",
                                            ),
                                        ),
                                        QQButton(
                                            id="9",
                                            render_data=RenderData(label="9", visited_label="9", style=1),
                                            action=Action(
                                                type=1,
                                                permission=Permission(type=2),
                                                unsupport_tips="该版本暂不支持查看此消息，请升级至最新版本。",
                                            ),
                                        ),
                                    ]
                                ),
                            ]
                        )
                    )
                )
            ),
        )
