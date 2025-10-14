from nonebot.adapters.bilibili_live.message import AtSegment, EmoticonSegment, TextSegment

from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.segment import At, Emoji, Text


class BiliLiveMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.bililive

    @build("text")
    def text(self, seg: TextSegment):
        return Text(seg.data["text"])

    @build("at")
    def at(self, seg: AtSegment):
        return At("user", str(seg.user_id), seg.data.get("name"))

    @build("emoticon")
    def emoticon(self, seg: EmoticonSegment):
        return Emoji(seg.data["emoji"], seg.data.get("descript"))
