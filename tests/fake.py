from datetime import datetime
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from nonebot.adapters.discord.event import ApplicationCommandInteractionEvent
    from nonebot.adapters.onebot.v11 import GroupMessageEvent as GroupMessageEventV11
    from nonebot.adapters.onebot.v12 import GroupMessageEvent as GroupMessageEventV12
    from nonebot.adapters.onebot.v11 import PrivateMessageEvent as PrivateMessageEventV11
    from nonebot.adapters.onebot.v12 import PrivateMessageEvent as PrivateMessageEventV12


def fake_group_message_event_v11(**field) -> "GroupMessageEventV11":
    from pydantic import create_model
    from nonebot.adapters.onebot.v11.event import Sender
    from nonebot.adapters.onebot.v11 import Message, GroupMessageEvent

    _Fake = create_model("_Fake", __base__=GroupMessageEvent)

    class FakeEvent(_Fake):
        time: int = 1000000
        self_id: int = 1
        post_type: Literal["message"] = "message"
        sub_type: str = "normal"
        user_id: int = 10
        message_type: Literal["group"] = "group"
        group_id: int = 10000
        message_id: int = 1
        message: Message = Message("test")
        raw_message: str = "test"
        font: int = 0
        sender: Sender = Sender(
            card="",
            nickname="test",
            role="member",
        )
        to_me: bool = False

        class Config:
            extra = "forbid"

    return FakeEvent(**field)


def fake_private_message_event_v11(**field) -> "PrivateMessageEventV11":
    from pydantic import create_model
    from nonebot.adapters.onebot.v11.event import Sender
    from nonebot.adapters.onebot.v11 import Message, PrivateMessageEvent

    _Fake = create_model("_Fake", __base__=PrivateMessageEvent)

    class FakeEvent(_Fake):
        time: int = 1000000
        self_id: int = 1
        post_type: Literal["message"] = "message"
        sub_type: str = "friend"
        user_id: int = 10
        message_type: Literal["private"] = "private"
        message_id: int = 1
        message: Message = Message("test")
        raw_message: str = "test"
        font: int = 0
        sender: Sender = Sender(nickname="test")
        to_me: bool = False

        class Config:
            extra = "forbid"

    return FakeEvent(**field)


def fake_group_message_event_v12(**field) -> "GroupMessageEventV12":
    from pydantic import create_model
    from nonebot.adapters.onebot.v12.event import BotSelf
    from nonebot.adapters.onebot.v12 import Message, GroupMessageEvent

    _Fake = create_model("_Fake", __base__=GroupMessageEvent)

    class FakeEvent(_Fake):
        self: BotSelf = BotSelf(platform="qq", user_id="test")
        id: str = "1"
        time: datetime = datetime.fromtimestamp(1000000)
        type: Literal["message"] = "message"
        detail_type: Literal["group"] = "group"
        sub_type: str = ""
        message_id: str = "10"
        message: Message = Message("test")
        original_message: Message = Message("test")
        alt_message: str = "test"
        user_id: str = "100"
        group_id: str = "10000"
        to_me: bool = False

        class Config:
            extra = "forbid"

    return FakeEvent(**field)


def fake_private_message_event_v12(**field) -> "PrivateMessageEventV12":
    from pydantic import create_model
    from nonebot.adapters.onebot.v12.event import BotSelf
    from nonebot.adapters.onebot.v12 import Message, PrivateMessageEvent

    _Fake = create_model("_Fake", __base__=PrivateMessageEvent)

    class FakeEvent(_Fake):
        self: BotSelf = BotSelf(platform="qq", user_id="test")
        id: str = "1"
        time: datetime = datetime.fromtimestamp(1000000)
        type: Literal["message"] = "message"
        detail_type: Literal["private"] = "private"
        sub_type: str = ""
        message_id: str = "10"
        message: Message = Message("test")
        original_message: Message = Message("test")
        alt_message: str = "test"
        user_id: str = "100"
        to_me: bool = False

        class Config:
            extra = "forbid"

    return FakeEvent(**field)


def fake_discord_interaction_event(**field) -> "ApplicationCommandInteractionEvent":
    from pydantic import create_model
    from nonebot.adapters.discord.event import ApplicationCommandInteractionEvent

    _Fake = create_model("_Fake", __base__=ApplicationCommandInteractionEvent)
    field["type"] = 2
    field["id"] = 123456
    field["application_id"] = 123456789
    field["token"] = "sometoken"
    field["version"] = 1

    class FakeEvent(_Fake):
        pass

    return FakeEvent(**field)
