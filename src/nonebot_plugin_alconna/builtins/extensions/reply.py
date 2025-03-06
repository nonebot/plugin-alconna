from typing import Optional

from tarina import LRU
from arclet.alconna import Alconna
from nonebot.internal.adapter import Bot, Event

from nonebot_plugin_alconna.uniseg import reply_fetch
from nonebot_plugin_alconna import Reply, Extension, UniMessage


class ReplyRecordExtension(Extension):
    """
    用于将消息事件中的回复暂存在 extension 中，以在后续的处理中获取回复信息。

    推荐配合 matcher.got 使用

    Example:
        >>> from nonebot_plugin_alconna import MsgId, on_alconna
        >>> from nonebot_plugin_alconna.builtins.extensions import ReplyRecordExtension
        >>>
        >>> matcher = on_alconna("...", extensions=[ReplyRecordExtension()])
        >>>
        >>> @matcher.handle()
        >>> async def handle(msg_id: MsgId, ext: ReplyRecordExtension):
        >>>     if reply := ext.get_reply(msg_id):
        >>>         ...
        >>>     else:
        >>>         ...
    """

    @property
    def priority(self) -> int:
        return 13

    @property
    def id(self) -> str:
        return "builtins.extensions.reply:ReplyRecordExtension"

    def __init__(self):
        self.cache: LRU[str, Reply] = LRU(20)

    def get_reply(self, message_id: str) -> Optional[Reply]:
        return self.cache.get(message_id, None)

    async def receive_wrapper(self, bot: Bot, event: Event, command: Alconna, receive: UniMessage) -> UniMessage:
        if not (reply := await reply_fetch(event, bot)):
            return receive
        msg_id = UniMessage.get_message_id(event, bot)
        self.cache[msg_id] = reply
        return receive


class ReplyMergeExtension(Extension):
    """
    用于将消息事件中的回复指向的原消息合并到当前消息中作为一部分参数

    推荐配合 matcher.got 使用

    Example:
        >>> from nonebot_plugin_alconna import Match, on_alconna
        >>> from nonebot_plugin_alconna.builtins.extensions.reply import ReplyMergeExtension
        >>>
        >>> matcher = on_alconna("...", extensions=[ReplyMergeExtension()])
        >>>
        >>> @matcher.handle()
        >>> async def handle(content: Match[str]):
        >>>     ...
    """

    def __init__(self, add_left: bool = False, sep: str = " "):
        """
        Args:
            add_left: 是否在当前消息的左侧合并回复消息，默认为 False
            sep: 合并时的分隔符，默认为空格
        """
        self.add_left = add_left
        self.sep = sep

    cache: "LRU[str, UniMessage]" = LRU(20)

    @property
    def priority(self) -> int:
        return 14

    @property
    def id(self) -> str:
        return "builtins.extensions.reply:ReplyMergeExtension"

    async def message_provider(self, event, state, bot, use_origin: bool = False):
        if event.get_type() != "message":
            return None
        try:
            msg = event.get_message()
        except (NotImplementedError, ValueError):
            return None
        msg_id = UniMessage.get_message_id(event, bot)
        if msg_id in self.cache:
            return self.cache[msg_id]
        uni_msg = UniMessage.generate_sync(message=msg, bot=bot)
        self.cache[msg_id] = uni_msg
        if not (reply := await reply_fetch(event, bot)):
            return uni_msg
        if not reply.msg:
            return uni_msg
        reply_msg = reply.msg
        if isinstance(reply_msg, str):
            reply_msg = msg.__class__(reply_msg)
        uni_msg_reply = UniMessage.generate_sync(message=reply_msg, bot=bot)
        if self.add_left:
            uni_msg_reply += self.sep
            uni_msg_reply.extend(uni_msg)
            self.cache[msg_id] = uni_msg_reply
            return uni_msg_reply
        uni_msg += self.sep
        uni_msg.extend(uni_msg_reply)
        self.cache[msg_id] = uni_msg
        return uni_msg


__extension__ = ReplyMergeExtension
