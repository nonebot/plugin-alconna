from nonebot import require
from arclet.alconna import Args, Alconna

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna.uniseg import reply_fetch
from nonebot_plugin_alconna import Extension, UniMessage, on_alconna


class ReplyExtension(Extension):
    @property
    def priority(self) -> int:
        return 14

    @property
    def id(self) -> str:
        return "reply"

    async def message_provider(self, event, state, bot, use_origin: bool = False):
        try:
            msg = event.get_message()
        except ValueError:
            return
        if not (reply := await reply_fetch(event, bot)):
            return None
        uni_msg_reply = UniMessage()
        if reply.msg:
            reply_msg = reply.msg
            if isinstance(reply_msg, str):
                reply_msg = msg.__class__(reply_msg)
            uni_msg_reply = UniMessage.generate_without_reply(message=reply_msg, bot=bot)
        uni_msg = UniMessage.generate_without_reply(message=msg, bot=bot)
        uni_msg += " "
        uni_msg.extend(uni_msg_reply)
        return uni_msg


preview = on_alconna(
    Alconna(
        "preview",
        Args["content", str],
    ),
    extensions=[ReplyExtension],
)


@preview.handle()
async def preview_h(content: str):
    await preview.finish(f"rendering preview: {content}")

