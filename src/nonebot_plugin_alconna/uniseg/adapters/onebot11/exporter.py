from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11.bot import Bot as OnebotBot
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from tarina import lang

from nonebot_plugin_alconna.uniseg.constraint import SupportScope, log
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter, SerializeFailed, SupportAdapter, Target, export
from nonebot_plugin_alconna.uniseg.segment import (
    At,
    AtAll,
    Audio,
    Emoji,
    File,
    Hyper,
    Image,
    Reference,
    RefNode,
    Reply,
    Text,
    Video,
    Voice,
)


class Onebot11MessageExporter(MessageExporter["Message"]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.onebot11

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if (group_id := getattr(event, "group_id", None)) is not None:
            return Target(
                str(group_id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        if (user_id := getattr(event, "user_id", None)) is not None:
            return Target(
                str(user_id),
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        if (message_id := getattr(event, "message_id", None)) is not None:
            return str(message_id)
        raise NotImplementedError

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag != "user":
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="at", seg=seg))
        return MessageSegment.at(seg.target)

    @export
    async def at_all(self, seg: AtAll, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.at("all")

    @export
    async def emoji(self, seg: Emoji, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.face(int(seg.id))

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio], bot: Union[Bot, None]) -> "MessageSegment":
        name = seg.__class__.__name__.lower()
        method = {
            "image": MessageSegment.image,
            "voice": MessageSegment.record,
            "video": MessageSegment.video,
            "audio": MessageSegment.record,
        }[name]
        if seg.raw:
            ans = method(seg.raw_bytes)
        elif seg.path:
            ans = method(Path(seg.path))
        elif seg.url:
            ans = method(seg.url)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))
        if isinstance(seg, Image) and seg.sticker:
            # 傻逼玩意，谁爱用用去
            # assert isinstance(bot, OnebotBot)
            # info = await bot.get_version_info()
            # app_name = info["app_name"]
            # if app_name == "NapCat.Onebot":
            #     ans.data["sub_type"] = 1
            # else:
            ans.data["subType"] = 1
        return ans

    @export
    async def file(self, seg: File, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.path:
            return MessageSegment(
                "$onebot11:file",
                {
                    "file": Path(seg.path).resolve(),
                    "name": Path(seg.path).name if seg.name == seg.__default_name__ else seg.name,
                },
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="file", seg=seg))

    @export
    async def hyper(self, seg: Hyper, bot: Union[Bot, None]) -> "MessageSegment":
        assert seg.raw, lang.require("nbp-uniseg", "invalid_segment").format(type="hyper", seg=seg)
        return MessageSegment.xml(seg.raw) if seg.format == "xml" else MessageSegment.json(seg.raw)

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.reply(int(seg.id))

    @export
    async def reference(self, seg: Reference, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.id:
            return MessageSegment.forward(seg.id)

        if not seg.children:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="forward", seg=seg))

        nodes = []
        for node in seg.children:
            if isinstance(node, RefNode):
                nodes.append(MessageSegment.node(int(node.id)))
            else:
                content = self.get_message_type()()
                if isinstance(node.content, str):
                    content.extend(self.get_message_type()(node.content))
                else:
                    content.extend(await self.export(node.content, bot, True))
                nodes.append(
                    MessageSegment.node_custom(
                        user_id=int(node.uid),
                        nickname=node.name,
                        content=content,  # type: ignore
                    )
                )
        return nodes  # type: ignore

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, OnebotBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, Event):
            _target = self.get_target(target, bot)
        else:
            _target = target

        if msg := message.include("node"):
            if _target.private:
                return await bot.call_api(
                    "send_private_forward_msg",
                    user_id=int(_target.id),
                    messages=msg,
                )
            return await bot.call_api(
                "send_group_forward_msg",
                group_id=int(_target.id),
                messages=msg,
            )
        if msg := message.include("$onebot11:file"):
            if _target.private:
                return await bot.call_api(
                    "upload_private_file",
                    user_id=int(_target.id),
                    file=msg[0].data["file"].as_posix(),
                    name=msg[0].data["name"],
                    **kwargs,
                )
            return await bot.call_api(
                "upload_group_file",
                group_id=int(_target.id),
                file=msg[0].data["file"].as_posix(),
                name=msg[0].data["name"],
                **kwargs,
            )
        if isinstance(target, Event):
            return await bot.send(target, message, **kwargs)  # type: ignore
        if _target.private:
            if _target.parent_id:
                return await bot.send_msg(
                    message_type="private",
                    user_id=int(_target.id),
                    group_id=int(_target.parent_id),
                    message=message,
                    **kwargs,
                )
            return await bot.send_msg(message_type="private", user_id=int(_target.id), message=message, **kwargs)
        return await bot.send_msg(message_type="group", group_id=int(_target.id), message=message, **kwargs)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, OnebotBot)
        if isinstance(mid, dict) and "message_id" in mid:
            await bot.delete_msg(message_id=mid["message_id"])
        elif isinstance(mid, (str, int)):
            await bot.delete_msg(message_id=int(mid))
        elif not mid and hasattr(context, "message_id"):
            await bot.delete_msg(message_id=context.message_id)  # type: ignore

    async def reaction(self, emoji: Emoji, mid: Any, bot: Bot, context: Union[Target, Event], delete: bool = False):
        assert isinstance(bot, OnebotBot)
        info = await bot.get_version_info()
        app_name = info["app_name"]
        message_id = mid["message_id"] if isinstance(mid, dict) else mid
        if app_name == "LLOneBot":
            await bot.call_api(
                "unset_msg_emoji_like" if delete else "set_msg_emoji_like",
                message_id=int(message_id),
                emoji_id=emoji.id,
            )
        elif app_name == "Lagrange.OneBot":
            if isinstance(context, Target):
                if context.private or context.channel:
                    return
                group_id = int(context.id)
            else:
                if (group_id := getattr(context, "group_id", None)) is None:
                    return
                group_id = int(group_id)
            await bot.call_api(
                "set_group_reaction",
                group_id=group_id,
                message_id=int(message_id),
                code=emoji.id,
                is_add=not delete,
            )
        elif app_name == "NapCat.Onebot":
            await bot.call_api(
                "set_msg_emoji_like",
                message_id=int(message_id),
                emoji_id=emoji.id,
                set=not delete,
            )
        elif app_name == "ws-plugin":
            if isinstance(context, Target):
                if context.private or context.channel:
                    return
                group_id = int(context.id)
            else:
                if (group_id := getattr(context, "group_id", None)) is None:
                    return
                group_id = int(group_id)
            assert emoji.id.isdigit()
            # https://bot.q.qq.com/wiki/develop/api-v2/openapi/emoji/model.html#EmojiType
            emj_type = 1 if int(emoji.id) < 5000 else 2
            await bot.call_api(
                "set_reaction",
                group_id=group_id,
                message_id=int(message_id),
                code=emoji.id,
                is_add=not delete,
                type=emj_type,
            )
        else:
            log("WARNING", f"Unsupported Client: {app_name} for message reaction!")

    def get_reply(self, mid: Any):
        return Reply(str(mid["message_id"]))
