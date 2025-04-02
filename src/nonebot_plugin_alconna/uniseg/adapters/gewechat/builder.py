from nonebot.adapters import Bot, Event
from nonebot.adapters.gewechat.message import Message, MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import At, Text, AtAll, Emoji, Hyper, Image, Reply


class GeWeChatMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.gewechat

    @build("text")
    def text(self, seg: "MessageSegment"):
        return Text(seg.data["text"])

    @build("at")
    def at(self, seg: "MessageSegment"):
        return At("user", seg.data["wxid"], seg.data.get("nickname"))

    @build("at_all")
    def at_all(self, seg: "MessageSegment"):
        return AtAll()

    @build("image")
    def image(self, seg: "MessageSegment"):
        return Image(url=seg.data["imgUrl"])

    @build("emoji")
    def emoji(self, seg: "MessageSegment"):
        return Emoji(id=seg.data["emojiMd5"])

    @build("xml")
    def xml(self, seg: "MessageSegment"):
        return Hyper("xml", seg.data["xml"])

    async def extract_reply(self, event: Event, bot: Bot):
        from nonebot.adapters.gewechat.event import QuoteMessageEvent

        if isinstance(event, QuoteMessageEvent):
            reply_id = event.reply.id if event.reply else event.original_message["quote", 0].data["svrId"]
            return Reply(
                reply_id,
                event.reply.msg if event.reply else Message(event.original_message[0].data["content"]),
                origin=event,
            )
        return None
