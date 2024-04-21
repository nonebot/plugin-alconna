from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import File, Text, Hyper, Image, Reply, Video, Voice

if TYPE_CHECKING:
    from nonebot.adapters.ntchat.message import MessageSegment  # type: ignore


class NTChatMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.ntchat

    @build("text")
    def text(self, seg: MessageSegment):
        return Text(seg.data["content"])

    @build("image")
    def image(self, seg: MessageSegment):
        return Image(id=seg.data["file_path"], path=seg.data["file_path"])

    @build("video")
    def video(self, seg: MessageSegment):
        return Video(id=seg.data["file_path"], path=seg.data["file_path"])

    @build("voice")
    def voice(self, seg: MessageSegment):
        return Voice(id=seg.data["file_path"], path=seg.data["file_path"])

    @build("audio")
    def audio(self, seg: MessageSegment):
        return Voice(id=seg.data["file_path"], path=seg.data["file_path"])

    @build("file")
    def file(self, seg: MessageSegment):
        return File(id=seg.data["file_path"])

    @build("card")
    def card(self, seg: MessageSegment):
        return Hyper("json", content={"card_wxid": seg.data["card_wxid"]})

    @build("xml")
    def xml(self, seg: MessageSegment):
        return Hyper("xml", seg.data["xml"])

    async def extract_reply(self, event: Event, bot: Bot):
        from nonebot.adapters.ntchat.event import QuoteMessageEvent  # type: ignore

        if TYPE_CHECKING:
            assert isinstance(event, QuoteMessageEvent)
        if event.type == 11061:  # type: ignore
            return Reply(event.quote_message_id, origin=event)  # type: ignore
