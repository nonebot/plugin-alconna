def test_mc_style_text():
    from nonebot.adapters.minecraft.model import TextColor
    from nonebot.adapters.minecraft.message import Message, MessageSegment

    from nonebot_plugin_alconna import Text, UniMessage

    msg = UniMessage([Text("1234").color("red", 0, 2).color("yellow"), Text("456").color("blue")])

    assert msg.export_sync(adapter="Minecraft") == Message(
        [
            MessageSegment.text("12", color=TextColor.RED),
            MessageSegment.text("34", color=TextColor.YELLOW),
            MessageSegment.text("456", color=TextColor.BLUE),
        ]
    )
