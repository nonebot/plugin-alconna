from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.kritor.bot import Bot as KritorBot
from nonebot.adapters.kritor.model import Contact, SceneType
from nonebot.adapters.kritor.message import Message, MessageSegment
from nonebot.adapters.kritor.protos.kritor.common import Button as ButtonModel
from nonebot.adapters.kritor.protos.kritor.message import SendMessageResponse, SendMessageByResIdResponse
from nonebot.adapters.kritor.event import MessageEvent, GroupApplyRequest, FriendApplyRequest, InvitedJoinGroupRequest
from nonebot.adapters.kritor.protos.kritor.common import (
    Sender,
    ButtonAction,
    ButtonRender,
    PushMessageBody,
    ForwardMessageBody,
    ButtonActionPermission,
)

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export
from nonebot_plugin_alconna.uniseg.segment import (
    At,
    Text,
    AtAll,
    Audio,
    Emoji,
    Hyper,
    Image,
    Reply,
    Video,
    Voice,
    Button,
    RefNode,
    Keyboard,
    Reference,
)


class KritorMessageExporter(MessageExporter["Message"]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.kritor

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if isinstance(event, MessageEvent):
            if event.contact.type is SceneType.GROUP:
                return Target(
                    str(event.contact.id),
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    scope=SupportScope.qq_client,
                )
            if event.contact.type in (SceneType.FRIEND, SceneType.STRANGER, SceneType.NEARBY):
                return Target(
                    str(event.contact.id),
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    scope=SupportScope.qq_client,
                )
            if event.contact.type is SceneType.GUILD:
                return Target(
                    str(event.contact.sub_id),
                    parent_id=str(event.contact.id),
                    channel=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    scope=SupportScope.qq_guild,
                )
            if event.contact.type is SceneType.STRANGER_FROM_GROUP:
                return Target(
                    str(event.sender.uin or event.sender.uid),
                    parent_id=str(event.contact.id),
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    scope=SupportScope.qq_client,
                )
        elif isinstance(event, FriendApplyRequest):
            return Target(
                str(event.applier_uin or event.applier_uid),
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        elif isinstance(event, GroupApplyRequest):
            return Target(
                str(event.applier_uin or event.applier_uid),
                parent_id=str(event.group_id),
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        elif isinstance(event, InvitedJoinGroupRequest):
            return Target(
                str(event.group_id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.message_id)

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.extract_most_style() == "markdown":
            return MessageSegment.markdown(seg.text)
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
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
            "voice": MessageSegment.voice,
            "video": MessageSegment.video,
            "audio": MessageSegment.voice,
        }[name]
        if seg.raw:
            return method(raw=seg.raw_bytes)
        elif seg.path:
            return method(path=Path(seg.path))
        elif seg.url:
            return method(url=seg.url)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def hyper(self, seg: Hyper, bot: Union[Bot, None]) -> "MessageSegment":
        assert seg.raw, lang.require("nbp-uniseg", "invalid_segment").format(type="hyper", seg=seg)
        return MessageSegment.xml(seg.raw) if seg.format == "xml" else MessageSegment.json(seg.raw)

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.reply(seg.id)

    @export
    async def reference(self, seg: Reference, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.id:
            return MessageSegment("$kritor:forward", {"res_id": seg.id})

        if not seg.children:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="forward", seg=seg))

        nodes = []
        for node in seg.children:
            if isinstance(node, RefNode):
                nodes.append(ForwardMessageBody(message_id=node.id))
            else:
                content = self.get_message_type()()
                if isinstance(node.content, str):
                    content.extend(self.get_message_type()(node.content))
                elif isinstance(node.content, list):
                    content.extend(await self.export(node.content, bot, True))  # type: ignore
                else:
                    content.extend(node.content)
                nodes.append(
                    ForwardMessageBody(
                        message=PushMessageBody(
                            time=int(node.time.timestamp()),
                            sender=Sender(uid=node.uid, uin=int(node.uid), nick=node.name),
                            elements=content.to_elements(),
                        )
                    )
                )
        return MessageSegment("$kritor:forward", {"nodes": nodes})

    def _button(self, seg: Button, bot: Union[Bot, None]):
        if seg.permission == "all":
            perm = ButtonActionPermission(type=2)
        elif seg.permission == "admin":
            perm = ButtonActionPermission(type=1)
        elif seg.permission[0].flag == "role":
            perm = ButtonActionPermission(type=3, role_ids=[i.target for i in seg.permission])
        else:
            perm = ButtonActionPermission(type=0, user_ids=[i.target for i in seg.permission])
        label = str(seg.label)
        return ButtonModel(
            id=seg.id or label,
            render_data=ButtonRender(
                label=label,
                visited_label=seg.clicked_label or label,
                style=0 if seg.style == "secondary" else 1,
            ),
            action=ButtonAction(
                type=0 if seg.flag == "link" else 1 if seg.flag == "action" else 2,
                data=seg.url or seg.text or label,
                enter=seg.flag == "enter",
                unsupported_tips="该版本暂不支持查看此消息，请升级至最新版本。",
                permission=perm,
            ),
        )

    @export
    async def button(self, seg: Button, bot: Union[Bot, None]):
        return MessageSegment("$kritor:button", {"button": self._button(seg, bot)})

    @export
    async def keyboard(self, seg: Keyboard, bot: Union[Bot, None]):
        if not seg.children or not seg.id:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="keyboard", seg=seg))
        if len(seg.children) > 25:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="keyboard", seg=seg))
        buttons = [self._button(child, bot) for child in seg.children]
        if len(buttons) < 6 and not seg.row:
            return MessageSegment("$kritor:button_row", {"buttons": buttons})
        return MessageSegment.keyboard(
            int(seg.id), [buttons[i : i + (seg.row or 5)] for i in range(0, len(buttons), seg.row or 5)]
        )

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, KritorBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, Event):
            _target = self.get_target(target, bot)
        else:
            _target = target

        if msg := message.include("$kritor:forward"):
            seg = msg[0]
            if _target.private:
                contact = Contact(scene=SceneType.FRIEND, peer=_target.id, sub_peer=None)
            else:
                contact = Contact(scene=SceneType.GROUP, peer=_target.id, sub_peer=None)
            if "res_id" in seg.data:
                return await bot.send_message_by_res_id(res_id=seg.data["res_id"], contact=contact)
            for node in seg.data["nodes"]:
                node.message.contact = contact.dump()
            return await bot.send_forward_message(contact, seg.data["nodes"])
        kb = None
        if message.has("$kritor:button"):
            buttons = [seg.data["button"] for seg in message.get("$kritor:button")]
            message = message.exclude("$kritor:button")
            kb = MessageSegment.keyboard(int(bot.self_id), [buttons[i : i + 5] for i in range(0, len(buttons), 5)])
        if message.has("$kritor:button_row"):
            rows = [seg.data["buttons"] for seg in message.get("$kritor:button_row")]
            message = message.exclude("$kritor:button_row")
            if not kb:
                kb = MessageSegment.keyboard(int(bot.self_id), buttons=rows)
            else:
                kb.data["rows"] += rows
        if kb:
            message.append(kb)
        if isinstance(target, Event):
            return await bot.send(target, message, **kwargs)  # type: ignore
        if _target.private:
            return await bot.send_message(
                contact=Contact(scene=SceneType.FRIEND, peer=_target.id, sub_peer=None), elements=message.to_elements()
            )
        elif _target.channel:
            if not _target.parent_id:
                raise NotImplementedError
            return await bot.send_channel_message(
                guild_id=int(_target.parent_id), channel_id=int(_target.id), message=str(message), **kwargs
            )
        else:
            return await bot.send_message(
                contact=Contact(scene=SceneType.GROUP, peer=_target.id, sub_peer=None), elements=message.to_elements()
            )

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, KritorBot)
        assert isinstance(mid, (SendMessageByResIdResponse, SendMessageResponse))
        await bot.recall_message(message_id=mid.message_id)
        return

    def get_reply(self, mid: Any):
        return Reply(str(mid["message_id"]))
