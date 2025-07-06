from nonebot.adapters.efchat.message import At as AtSegment
from nonebot.adapters.efchat.message import Image as ImageSegment
from nonebot.adapters.efchat.message import Voice as VoiceSegment

from nonebot_plugin_alconna.uniseg.segment import At, Image, Voice
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build


class EFChatMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.efchat

    @build("at")
    def at(self, seg: AtSegment):
        return At("user", seg.data["target"])

    @build("image")
    def image(self, seg: ImageSegment):
        return Image(url=seg.data["url"])

    @build("voice")
    def voice(self, seg: VoiceSegment):
        return Voice(url=seg.data["url"], id=seg.data.get("src"))
