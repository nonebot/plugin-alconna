from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Message
from nonebot.internal.driver import Request

from .segment import (
    At,
    Card,
    File,
    Text,
    AtAll,
    Audio,
    Emoji,
    Image,
    Other,
    Reply,
    Video,
    Voice,
)

if TYPE_CHECKING:
    from .message import UniMessage


class SerializeFailed(Exception):
    ...


async def generate_bilibili_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.bilibili.message import Message as BM  # type: ignore

    message = BM()
    ms = message.get_segment_class()

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.danmu(seg.text))
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to bilibili message")
    return message


async def generate_console_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.console.message import Message as ConsoleMessage

    message = ConsoleMessage()
    ms = message.get_segment_class()

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.text(seg.text))
        elif isinstance(seg, Emoji):
            message.append(ms.emoji(seg.name or seg.id))
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to console message")
    return message


async def generate_ding_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.ding.message import Message as DingMessage

    message = DingMessage()
    ms = message.get_segment_class()

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.text(seg.text))
        elif isinstance(seg, At):
            message.append(ms.atDingtalkIds(seg.target))
        elif isinstance(seg, AtAll):
            message.append(ms.atAll())
        elif isinstance(seg, Image):
            assert seg.url, "ding image segment must have url"
            message.append(ms.image(seg.url))
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to ding message")
    return message


async def generate_discord_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.discord.message import Message as DiscordMessage

    message = DiscordMessage()
    ms = message.get_segment_class()

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.text(seg.text))
        elif isinstance(seg, Emoji):
            message.append(ms.custom_emoji(seg.name or "", seg.id))
        elif isinstance(seg, (Image, Voice, Video, Audio)):
            if seg.raw:
                message.append(ms.attachment(seg.id or seg.name, content=seg.raw))
            elif seg.path:
                path = Path(seg.path)
                message.append(ms.attachment(path.name, content=path.read_bytes()))
            elif seg.url:
                resp = await bot.adapter.request(Request("GET", seg.url))
                message.append(
                    ms.attachment(
                        seg.id or seg.name,
                        content=resp.content,  # type: ignore
                    )
                )
            else:
                raise SerializeFailed(f"Invalid image segment: {seg!r}")
        elif isinstance(seg, File):
            if not seg.raw:
                raise SerializeFailed(f"Invalid file segment: {seg!r}")
            message.append(ms.attachment(seg.name, content=seg.raw))  # type: ignore
        elif isinstance(seg, At):
            if seg.type == "role":
                message.append(ms.mention_role(int(seg.target)))
            elif seg.type == "channel":
                message.append(ms.mention_channel(int(seg.target)))
            else:
                message.append(ms.mention_user(int(seg.target)))
        elif isinstance(seg, AtAll):
            message.append(ms.mention_everyone())
        elif isinstance(seg, Reply):
            message.append(ms.reference(seg.origin or int(seg.id)))
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to discord message")
    return message


async def generate_feishu_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.feishu.message import MessageSegment
    from nonebot.adapters.feishu.message import Message as FeishuMessage

    message = FeishuMessage()
    ms = MessageSegment

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.text(seg.text))
        elif isinstance(seg, At):
            message.append(ms.at(seg.target))
        elif isinstance(seg, Image):
            if seg.id:
                message.append(ms.image(seg.id))
            else:
                if seg.url:
                    resp = await bot.adapter.request(Request("GET", seg.url))
                    image = resp.content
                elif seg.path:
                    image = Path(seg.path).read_bytes()
                elif seg.raw:
                    image = seg.raw
                else:
                    raise SerializeFailed(f"Invalid image segment: {seg!r}")
                data = {"image_type": "message"}
                files = {"image": ("file", image)}
                params = {"method": "POST", "data": data, "files": files}
                result = await bot.call_api("im/v1/images", **params)
                file_key = result["image_key"]
                message.append(ms.image(file_key))
        elif isinstance(seg, (Voice, Audio)):
            name = seg.__class__.__name__.lower()
            if seg.id:
                message.append(ms.audio(seg.id))
            else:
                if seg.url:
                    resp = await bot.adapter.request(Request("GET", seg.url))
                    audio = resp.content
                elif seg.path:
                    audio = Path(seg.path).read_bytes()
                elif seg.raw:
                    audio = seg.raw
                else:
                    raise SerializeFailed(f"Invalid {name} segment: {seg!r}")
                data = {"file_type": "stream", "file_name": seg.name}
                files = {"file": ("file", audio)}
                params = {"method": "POST", "data": data, "files": files}
                result = await bot.call_api("im/v1/files", **params)
                file_key = result["file_key"]
                message.append(ms.audio(file_key))
        elif isinstance(seg, File):
            if seg.id:
                message.append(ms.file(seg.id, seg.name))  # type: ignore
            elif seg.raw and seg.name:
                data = {"file_type": "stream", "file_name": seg.name}
                files = {"file": ("file", seg.raw)}
                params = {"method": "POST", "data": data, "files": files}
                result = await bot.call_api("im/v1/files", **params)
                file_key = result["file_key"]
                message.append(ms.file(file_key))
            else:
                raise SerializeFailed(f"Invalid file segment: {seg!r}")
        elif isinstance(seg, Reply):
            message.append(ms("reply", {"message_id": seg.id}))
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to feishu message")
    return message


async def generate_github_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.github.message import Message as GithubMessage  # type: ignore

    message = GithubMessage()
    ms = message.get_segment_class()

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.text(seg.text))
        elif isinstance(seg, At):
            message.append(ms.text(f"@{seg.target}"))
        elif isinstance(seg, Image):
            if seg.url:
                message.append(ms.text(f"![]({seg.url})"))
            else:
                raise SerializeFailed(f"Invalid image segment: {seg!r}")
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to github message")
    return message


async def generate_kook_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.kaiheila.message import MessageSegment
    from nonebot.adapters.kaiheila.message import Message as KookMessage

    if TYPE_CHECKING:
        from nonebot.adapters.kaiheila.bot import Bot as KookBot

        assert isinstance(bot, KookBot)

    message = KookMessage()
    ms = MessageSegment

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.text(seg.text))
        elif isinstance(seg, At):
            if seg.type == "role":
                message.append(ms.KMarkdown(f"(rol){seg.target}(rol)"))
            elif seg.type == "channel":
                message.append(ms.KMarkdown(f"(chn){seg.target}(chn)"))
            else:
                message.append(ms.KMarkdown(f"(met){seg.target}(met)"))
        elif isinstance(seg, AtAll):
            message.append(ms.KMarkdown("(met)all(met)"))
        elif isinstance(seg, Emoji):
            if seg.name:
                message.append(ms.KMarkdown(f"(emj){seg.name}(emj)[{seg.id}]"))
            else:
                message.append(ms.KMarkdown(f":{seg.id}:"))
        elif isinstance(seg, (Image, Voice, Audio, Video)):
            name = seg.__class__.__name__.lower()
            method = {
                "image": ms.image,
                "voice": ms.audio,
                "audio": ms.audio,
                "video": ms.video,
            }[name]
            if seg.id or seg.url:
                message.append(method(seg.id or seg.url))
            elif seg.path or seg.raw:
                file_key = await bot.upload_file(seg.path or seg.raw)  # type: ignore
                message.append(method(file_key))
            else:
                raise SerializeFailed(f"Invalid {name} segment: {seg!r}")
        elif isinstance(seg, Card):
            if seg.type == "xml":
                raise SerializeFailed("Cannot serialize xml card to kook message")
            message.append(ms.Card(seg.raw))  # type: ignore
        elif isinstance(seg, Reply):
            message.append(ms.quote(seg.id))
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to kook message")

    return message


async def generate_minecraft_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.minecraft.message import MessageSegment
    from nonebot.adapters.minecraft.message import Message as MinecraftMessage

    message = MinecraftMessage()
    ms = MessageSegment

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.text(seg.text))
        elif isinstance(seg, At):
            message.append(ms.text(f"@{seg.target}"))
        elif isinstance(seg, (Image, Video)):
            name = seg.__class__.__name__.lower()
            if not seg.id and not seg.url:
                raise SerializeFailed(f"Invalid {name} segment: {seg!r}")
            method = {
                "image": ms.image,
                "video": ms.video,
            }[name]
            message.append(method(seg.id or seg.url))  # type: ignore
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to minecraft message")

    return message


async def generate_mirai_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.mirai2.message import MessageType
    from nonebot.adapters.mirai2.message import MessageSegment
    from nonebot.adapters.mirai2.message import MessageChain as MiraiMessage

    if TYPE_CHECKING:
        from nonebot.adapters.mirai2.bot import Bot as MiraiBot

        assert isinstance(bot, MiraiBot)

    message = MiraiMessage([])
    ms = MessageSegment

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.plain(seg.text))
        elif isinstance(seg, At):
            message.append(ms.at(int(seg.target)))
        elif isinstance(seg, AtAll):
            message.append(ms.at_all())
        elif isinstance(seg, Emoji):
            message.append(ms.face(int(seg.id), seg.name))
        elif isinstance(seg, (Image, Voice, Audio)):
            name = seg.__class__.__name__.lower()
            method = {
                "image": ms.image,
                "voice": ms.voice,
                "audio": ms.voice,
            }[name]
            if seg.id:
                message.append(method(seg.id))
            elif seg.url:
                message.append(method(url=seg.url))
            elif seg.path:
                message.append(method(path=str(seg.path)))
            else:
                raise SerializeFailed(f"Invalid {name} segment: {seg!r}")
        elif isinstance(seg, File):
            message.append(ms.file(seg.id, seg.name, 0))  # type: ignore
        elif isinstance(seg, Card):
            if seg.type == "xml":
                message.append(ms.xml(seg.raw))  # type: ignore
            else:
                message.append(ms.app(seg.raw))  # type: ignore
        elif isinstance(seg, Reply):
            message.append(ms(MessageType.QUOTE, id=seg.id))
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.plain(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to mirai message")
    return message


async def generate_onebot11_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.onebot.v11.message import MessageSegment
    from nonebot.adapters.onebot.v11.message import Message as OneBot11Message

    if TYPE_CHECKING:
        from nonebot.adapters.onebot.v11.bot import Bot as OneBot11Bot

        assert isinstance(bot, OneBot11Bot)

    message = OneBot11Message()
    ms = MessageSegment

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.text(seg.text))
        elif isinstance(seg, At):
            message.append(ms.at(seg.target))
        elif isinstance(seg, AtAll):
            message.append(ms.at("all"))
        elif isinstance(seg, Emoji):
            message.append(ms.face(int(seg.id)))
        elif isinstance(seg, (Image, Voice, Video, Audio)):
            name = seg.__class__.__name__.lower()
            method = {
                "image": ms.image,
                "voice": ms.record,
                "video": ms.video,
                "audio": ms.record,
            }[name]
            if seg.raw:
                message.append(method(seg.raw))
            elif seg.path:
                message.append(method(Path(seg.path)))
            elif seg.url:
                resp = await bot.adapter.request(Request("GET", seg.url))
                message.append(method(resp.content))
            elif seg.id:
                message.append(method(seg.id))
            else:
                raise SerializeFailed(f"Invalid {name} segment: {seg!r}")
        elif isinstance(seg, Card):
            if seg.type == "xml":
                message.append(ms.xml(seg.raw))  # type: ignore
            else:
                message.append(ms.json(seg.raw))  # type: ignore
        elif isinstance(seg, Reply):
            message.append(ms.reply(int(seg.id)))
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to onebot11 message")

    return message


async def generate_onebot12_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.onebot.v12.message import Message as OneBot12Message

    if TYPE_CHECKING:
        from nonebot.adapters.onebot.v12.bot import Bot as OneBot12Bot

        assert isinstance(bot, OneBot12Bot)

    message = OneBot12Message()
    ms = message.get_segment_class()

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.text(seg.text))
        elif isinstance(seg, At):
            message.append(ms.mention(seg.target))
        elif isinstance(seg, AtAll):
            message.append(ms.mention_all())
        elif isinstance(seg, (Image, Voice, Video, Audio)):
            name = seg.__class__.__name__.lower()
            method = {
                "image": ms.image,
                "voice": ms.voice,
                "video": ms.video,
                "audio": ms.audio,
            }[name]
            if seg.id:
                message.append(method(seg.id))
            elif seg.url:
                resp = await bot.upload_file(type="url", name=seg.name, url=seg.url)
                message.append(method(resp["file_id"]))
            elif seg.path:
                resp = await bot.upload_file(type="path", name=seg.name, path=str(seg.path))
                message.append(method(resp["file_id"]))
            elif seg.raw:
                resp = await bot.upload_file(type="data", name=seg.name, data=seg.raw)
                message.append(method(resp["file_id"]))
            else:
                raise SerializeFailed(f"Invalid {name} segment: {seg!r}")
        elif isinstance(seg, File):
            if seg.id:
                message.append(ms.file(seg.id))
            elif seg.raw:
                resp = await bot.upload_file(type="data", name=seg.name or "file", data=seg.raw)
                message.append(ms.file(resp["file_id"]))
            else:
                raise SerializeFailed(f"Invalid file segment: {seg!r}")
        elif isinstance(seg, Reply):
            message.append(ms.reply(seg.id))
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to onebot12 message")

    return message


async def generate_qqguild_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.qqguild.message import MessageSegment
    from nonebot.adapters.qqguild.message import Message as QQGuildMessage

    message = QQGuildMessage()
    ms = MessageSegment

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.text(seg.text))
        elif isinstance(seg, At):
            if seg.target == "channel":
                message.append(ms.mention_channel(int(seg.target)))
            elif seg.target == "user":
                message.append(ms.mention_user(int(seg.target)))
            else:
                raise SerializeFailed(f"Cannot serialize {seg!r} to qqguild mention")
        elif isinstance(seg, AtAll):
            message.append(ms.mention_everyone())
        elif isinstance(seg, Emoji):
            message.append(ms.emoji(seg.id))
        elif isinstance(seg, Image):
            if seg.url:
                message.append(ms.image(seg.url))
            elif seg.raw or seg.path:
                message.append(ms.file_image(seg.raw or Path(seg.path)))  # type: ignore
            else:
                raise SerializeFailed(f"Invalid image segment: {seg!r}")
        elif isinstance(seg, Reply):
            message.append(ms.reference(seg.id))
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to qqguild message")

    return message


async def generate_red_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.red.message import MessageSegment
    from nonebot.adapters.red.message import Message as RedMessage

    message = RedMessage()
    ms = MessageSegment

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.text(seg.text))
        elif isinstance(seg, At):
            message.append(ms.at(seg.target))
        elif isinstance(seg, AtAll):
            message.append(ms.at_all())
        elif isinstance(seg, Emoji):
            message.append(ms.face(seg.id))
        elif isinstance(seg, (Image, Voice, Video, Audio)):
            name = seg.__class__.__name__.lower()
            method = {
                "image": ms.image,
                "voice": ms.voice,
                "video": ms.video,
                "audio": ms.voice,
            }[name]
            if seg.raw or seg.path:
                message.append(method(seg.raw or Path(seg.path)))  # type: ignore
            elif seg.url:
                resp = await bot.adapter.request(Request("GET", seg.url))
                message.append(method(resp.content))  # type: ignore
            else:
                raise SerializeFailed(f"Invalid {name} segment: {seg!r}")
        elif isinstance(seg, File):
            message.append(ms.file(seg.raw))  # type: ignore
        elif isinstance(seg, Reply):
            message.append(ms.reply(seg.id))
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to red message")

    return message


async def generate_telegram_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.telegram.message import Entity
    from nonebot.adapters.telegram.message import File as TgFile
    from nonebot.adapters.telegram.message import MessageSegment
    from nonebot.adapters.telegram.message import Message as TelegramMessage

    message = TelegramMessage()

    for seg in source:
        if isinstance(seg, Text):
            if not seg.style:
                message.append(Entity.text(seg.text))
            else:
                message.append(Entity(seg.style, {"text": seg.text}))
        elif isinstance(seg, At):
            message.append(
                Entity.mention(f"{seg.target} ")
                if seg.target.startswith("@")
                else Entity.text_link("用户 ", f"tg://user?id={seg.target}")
            )
        elif isinstance(seg, Emoji):
            message.append(Entity.custom_emoji(seg.name, seg.id))  # type: ignore
        elif isinstance(seg, (Image, Voice, Video, Audio)):
            name = seg.__class__.__name__.lower()
            method = {
                "image": TgFile.photo,
                "voice": TgFile.voice,
                "video": TgFile.video,
                "audio": TgFile.audio,
            }[name]
            if seg.id or seg.url:
                message.append(method(seg.id or seg.url))
            elif seg.path:
                message.append(method(Path(seg.path).read_bytes()))
            elif seg.raw:
                message.append(method(seg.raw))
            else:
                raise SerializeFailed(f"Invalid {name} segment: {seg!r}")
        elif isinstance(seg, File):
            if seg.id:
                message.append(TgFile.document(seg.id))
            elif seg.raw:
                message.append(TgFile.document(seg.raw))
            else:
                raise SerializeFailed(f"Invalid file segment: {seg!r}")
        elif isinstance(seg, Reply):
            message.append(MessageSegment("reply", {"message_id": seg.id}))
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(Entity.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to telegram message")

    return message


async def generate_villa_message(source: "UniMessage", bot: Bot, fallback: bool) -> Message:
    from nonebot.adapters.villa.message import MessageSegment
    from nonebot.adapters.villa.message import Message as VillaMessage

    message = VillaMessage()
    ms = MessageSegment

    for seg in source:
        if isinstance(seg, Text):
            message.append(ms.text(seg.text))
        elif isinstance(seg, At):
            if seg.type == "user":
                message.append(ms.mention_user(int(seg.target), seg.display))
            elif seg.type == "channel":
                villa_id, room_id = seg.target.split(":", 1)
                message.append(ms.room_link(int(villa_id), int(room_id), seg.display))
            else:
                raise SerializeFailed(f"Invalid At segment: {seg!r}")
        elif isinstance(seg, AtAll):
            message.append(ms.mention_all())
        elif isinstance(seg, Image):
            if seg.url:
                message.append(ms.image(seg.url))
            else:
                raise SerializeFailed(f"Invalid image segment: {seg!r}")
        elif isinstance(seg, Reply):
            message.append(ms.quote(seg.id, int(datetime.now().timestamp())))
        elif isinstance(seg, Other):
            message.append(seg.origin)  # type: ignore
        elif fallback:
            message.append(ms.text(str(seg)))
        else:
            raise SerializeFailed(f"Cannot serialize {seg!r} to villa message")

    return message


MAPPING = {
    "BilibiliLive": generate_bilibili_message,
    "Console": generate_console_message,
    "Ding": generate_ding_message,
    "Discord": generate_discord_message,
    "Feishu": generate_feishu_message,
    "GitHub": generate_github_message,
    "Kaiheila": generate_kook_message,
    "Minecraft": generate_minecraft_message,
    "mirai2": generate_mirai_message,
    "OneBot V11": generate_onebot11_message,
    "OneBot V12": generate_onebot12_message,
    "QQ Guild": generate_qqguild_message,
    "RedProtocol": generate_red_message,
    "Telegram": generate_telegram_message,
    "Villa": generate_villa_message,
}
