from datetime import datetime
from typing import TYPE_CHECKING, Literal

from nonebot.compat import type_validate_python

if TYPE_CHECKING:
    from nonebot.adapters.qq import MessageCreateEvent as MessageCreateEvent
    from nonebot.adapters.satori.event import MessageEvent as SatoriMessageEvent
    from nonebot.adapters.discord.event import ApplicationCommandInteractionEvent
    from nonebot.adapters.onebot.v11 import GroupMessageEvent as GroupMessageEventV11
    from nonebot.adapters.onebot.v11 import PrivateMessageEvent as PrivateMessageEventV11
    from nonebot.adapters.discord.event import GuildMessageCreateEvent as DiscordMessageEvent


_msg_ids = iter(range(1000000))


def get_msg_id() -> int:
    return next(_msg_ids)


def fake_group_message_event_v11(**field) -> "GroupMessageEventV11":
    from pydantic import create_model
    from nonebot.adapters.onebot.v11.event import Sender
    from nonebot.adapters.onebot.v11 import Message, GroupMessageEvent

    _fake = create_model("_fake", __base__=GroupMessageEvent)

    class FakeEvent(_fake):
        time: int = 1000000
        self_id: int = 1
        post_type: Literal["message"] = "message"
        sub_type: str = "normal"
        user_id: int = 10
        message_type: Literal["group"] = "group"
        group_id: int = 10000
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

    return FakeEvent(message_id=get_msg_id(), **field)


def fake_private_message_event_v11(**field) -> "PrivateMessageEventV11":
    from pydantic import create_model
    from nonebot.adapters.onebot.v11.event import Sender
    from nonebot.adapters.onebot.v11 import Message, PrivateMessageEvent

    _fake = create_model("_fake", __base__=PrivateMessageEvent)

    class FakeEvent(_fake):
        time: int = 1000000
        self_id: int = 1
        post_type: Literal["message"] = "message"
        sub_type: str = "friend"
        user_id: int = 10
        message_type: Literal["private"] = "private"
        message: Message = Message("test")
        raw_message: str = "test"
        font: int = 0
        sender: Sender = Sender(nickname="test")
        to_me: bool = False

        class Config:
            extra = "forbid"

    return FakeEvent(message_id=get_msg_id(), **field)


def fake_discord_interaction_event(**field) -> "ApplicationCommandInteractionEvent":
    from pydantic import create_model
    from nonebot.adapters.discord.event import ApplicationCommandInteractionEvent

    _fake = create_model("_fake", __base__=ApplicationCommandInteractionEvent)
    field["type"] = 2
    field["id"] = get_msg_id() + 123456
    field["application_id"] = 123456789
    field["token"] = "sometoken"  # noqa: S105
    field["version"] = 1

    class FakeEvent(_fake):
        pass

    return FakeEvent(**field)


def fake_message_event_discord(content: str) -> "DiscordMessageEvent":
    from nonebot.adapters.discord.api import MessageFlag, MessageType
    from nonebot.adapters.discord.event import GuildMessageCreateEvent

    return type_validate_python(
        GuildMessageCreateEvent,
        {
            "id": get_msg_id() + 11234,
            "channel_id": 5566,
            "guild_id": 6677,
            "author": {
                "id": 3344,
                "username": "MyUser",
                "discriminator": "0",
                "avatar": "xxx",
            },
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
    from nonebot.adapters.satori.models import User, Login, Channel, ChannelType, LoginStatus, MessageObject

    _fake = create_model("_fake", __base__=MessageEvent)

    class FakeEvent(_fake):
        sn: int = 1
        type: str = "message-created"
        login: Login = Login(
            sn=0,
            adapter="test",
            status=LoginStatus.ONLINE,
            platform="satori",
            user=User(id="123456789", name="test"),
        )
        timestamp: datetime = datetime.fromtimestamp(1000000)  # noqa: DTZ006
        channel: Channel = Channel(id="1", type=ChannelType.TEXT)
        user: User = User(id="1", name="test")
        message: MessageObject = MessageObject(id="1", content="text")
        to_me: bool = False

        class Config:
            extra = "allow"

    _message = field.pop("message", Message("test"))
    _original_message = field.pop("original_message", _message)
    event = FakeEvent(message={"id": str(get_msg_id()), "content": "text"}, **field)  # type: ignore
    event._message = _message
    event.original_message = _original_message
    return event


def fake_message_event_guild(**field) -> "MessageCreateEvent":
    from pydantic import create_model
    from nonebot.adapters.qq.message import Message
    from nonebot.adapters.qq.models.guild import User
    from nonebot.adapters.qq.event import MessageCreateEvent

    _fake = create_model("_fake", __base__=MessageCreateEvent)

    class FakeEvent(_fake):
        channel_id: str = "abcd"
        guild_id: str = "efgh"
        content: str = "test"
        author: User = User(id=field.pop("user_id", "123456789"), username=field.pop("username", "foobar"))
        _message = field.pop("message", Message("test"))

        class Config:
            extra = "forbid"

    return FakeEvent(id=str(get_msg_id() + 5555), **field)


def fake_satori_bot_params(self_id: str = "test", platform: str = "test") -> dict:
    from nonebot.adapters.satori.models import User, Login, LoginStatus

    return {
        "self_id": self_id,
        "login": Login(
            sn=0,
            adapter="test",
            status=LoginStatus.ONLINE,
            platform=platform,
            user=User(id=self_id, name="test"),
        ),
        "info": None,
        "proxy_urls": [],
    }
