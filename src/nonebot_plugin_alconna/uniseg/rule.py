from nonebot.params import Depends
from nonebot.internal.rule import Rule
from nonebot.adapters import Bot, Event, Message

from .message import UniMessage
from .constraint import SupportScope
from .segment import At, Text, Reply


async def _get_message(event: Event, bot: Bot):
    if event.get_type() != "message":
        return None
    try:
        msg: Message = event.get_message()
    except (NotImplementedError, ValueError):
        return None
    try:
        msg: Message = getattr(event, "original_message", msg)  # type: ignore
    except (NotImplementedError, ValueError):
        pass
    return await UniMessage.generate(message=msg, bot=bot)


class AtInRule:

    def __init__(self, *target: str):
        self.targets = set(target)

    async def __call__(self, msg: UniMessage = Depends(_get_message)):
        if not msg:
            return False
        if isinstance(msg[0], Reply):
            msg.pop(0)
        if not msg or not isinstance(msg[0], At):
            return False
        at = msg[At, 0]
        if at.flag != "user":
            return False
        return at.target in self.targets


class AtMeRule:

    def __init__(self, only_at: bool = False):
        self.only = only_at

    async def __call__(self, event: Event, bot: Bot, msg: UniMessage = Depends(_get_message)):
        if not msg:
            return False
        if isinstance(msg[0], Reply):
            msg.pop(0)
        if not msg or not isinstance(msg[0], At):
            target = UniMessage.get_target(event=event, bot=bot)
            if target.scope is SupportScope.qq_api and not target.channel:  # QQ API 群聊下会吞 At
                msg.insert(0, At("user", bot.self_id))
            else:
                return False
        at = msg[At, 0]
        if at.flag != "user":
            return False
        ans = bot.self_id == at.target
        if self.only and len(msg) > 1:
            if not isinstance(msg[1], Text):
                return False
            text: Text = msg[Text, 0]
            if text.text.strip("\xa0").strip():
                return False
        return ans


def at_in(*target: str) -> Rule:
    return Rule(AtInRule(*target))


def at_me(only_at: bool = False) -> Rule:
    return Rule(AtMeRule(only_at))
