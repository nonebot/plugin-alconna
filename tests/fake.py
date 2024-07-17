from datetime import datetime
from typing import TYPE_CHECKING, Literal

from nonebot.compat import type_validate_python
from nonebot.adapters.satori.models import Login, LoginStatus

FAKE_SATORI_LOGIN = Login(status=LoginStatus.ONLINE)

if TYPE_CHECKING:
    from nonebot.adapters.qq import MessageCreateEvent as MessageCreateEvent
    from nonebot.adapters.satori.event import MessageEvent as SatoriMessageEvent
    from nonebot.adapters.discord.event import ApplicationCommandInteractionEvent
    from nonebot.adapters.onebot.v11 import GroupMessageEvent as GroupMessageEventV11
    from nonebot.adapters.onebot.v11 import PrivateMessageEvent as PrivateMessageEventV11
    from nonebot.adapters.discord.event import GuildMessageCreateEvent as DiscordMessageEvent


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
            extra = "allow"

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


def fake_message_event_discord(content: str) -> "DiscordMessageEvent":
    from nonebot.adapters.discord.api.model import User
    from nonebot.adapters.discord.api import MessageFlag, MessageType
    from nonebot.adapters.discord.event import GuildMessageCreateEvent

    return type_validate_python(
        GuildMessageCreateEvent,
        {
            "id": 11234,
            "channel_id": 5566,
            "guild_id": 6677,
            "author": User(
                **{
                    "id": 3344,
                    "username": "MyUser",
                    "discriminator": "0",
                    "avatar": "xxx",
                }
            ),
            "content": content,
            "timestamp": 123456,
            "edited_timestamp": None,
            "tts": False,
            "mention_everyone": False,
            "mentions": [],
            "mention_roles": [],
            "attachments": [],
            "embeds": [],
            "nonce": 3210,
            "pinned": False,
            "type": MessageType(0),
            "flags": MessageFlag(0),
            "referenced_message": None,
            "components": [],
            "to_me": False,
            "reply": None,
        },
    )


def fake_message_event_satori(**field) -> "SatoriMessageEvent":
    from pydantic import create_model
    from nonebot.adapters.satori import Message
    from nonebot.adapters.satori.event import MessageEvent
    from nonebot.adapters.satori.models import User, Channel, ChannelType, MessageObject

    _Fake = create_model("_Fake", __base__=MessageEvent)

    class FakeEvent(_Fake):
        id: int = 1
        type: str = "message-created"
        self_id: str = "123456789"
        platform: str = "satori"
        timestamp: datetime = datetime.fromtimestamp(1000000)
        channel: Channel = Channel(id="1", type=ChannelType.TEXT)
        user: User = User(id="1", name="test")
        message: MessageObject = MessageObject(id="1", content="text")
        to_me: bool = False

        class Config:
            extra = "allow"

    _message = field.pop("message", Message("test"))
    event = FakeEvent(message={"id": "1", "content": "text"}, **field)  # type: ignore
    event._message = _message
    event.original_message = _message
    return event


def fake_message_event_guild(**field) -> "MessageCreateEvent":
    from pydantic import create_model
    from nonebot.adapters.qq.message import Message
    from nonebot.adapters.qq.models.guild import User
    from nonebot.adapters.qq.event import MessageCreateEvent

    _Fake = create_model("_Fake", __base__=MessageCreateEvent)

    class FakeEvent(_Fake):
        id: str = "1234"
        channel_id: str = "abcd"
        guild_id: str = "efgh"
        content: str = "test"
        author: User = User(id=field.pop("user_id", "123456789"), username=field.pop("username", "foobar"))
        _message = field.pop("message", Message("test"))

        class Config:
            extra = "forbid"

    return FakeEvent(**field)
