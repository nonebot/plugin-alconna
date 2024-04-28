from typing import Optional

from tarina import LRU

from nonebot_plugin_alconna.uniseg import reply_fetch
from nonebot_plugin_alconna import Reply, Extension, UniMessage


class ReplyRecordExtension(Extension):
    """
    用于将消息事件中的回复暂存在 extension 中，使得解析用的消息不带回复信息，同时可以在后续的处理中获取回复信息。

    推荐配合 matcher.got 使用

    Example:
        ```python
        from nonebot_plugin_alconna import MsgId, on_alconna
        from nonebot_plugin_alconna.builtins.extensions import ReplyRecordExtension

        matcher = on_alconna(..., extensions=[ReplyRecordExtension()])

        @matcher.handle()
        async def handle(msg_id: MsgId, ext: ReplyRecordExtension):
            if reply := ext.get_reply(msg_id):
                ...
            else:
                ...
        ```
    """

    @property
    def priority(self) -> int:
        return 14

    @property
    def id(self) -> str:
        return "builtins.extensions.reply:ReplyRecordExtension"

    def __init__(self):
        self.cache: "LRU[str, Reply]" = LRU(20)

    def get_reply(self, message_id: str) -> Optional[Reply]:
        return self.cache.get(message_id, None)

    async def message_provider(self, event, state, bot, use_origin: bool = False):
        try:
            msg = event.get_message()
        except ValueError:
            return
        uni_msg = UniMessage.generate_without_reply(message=msg, bot=bot)
        if not (reply := await reply_fetch(event, bot)):
            return uni_msg
        msg_id = UniMessage.get_message_id(event, bot)
        self.cache[msg_id] = reply
        return uni_msg


__extension__ = ReplyRecordExtension
