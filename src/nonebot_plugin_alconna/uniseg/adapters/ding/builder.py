from nonebot.adapters.ding.message import MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import At, Text, AtAll, Image


class DingMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.ding

    @build("text")
    def text(self, seg: MessageSegment):
        return Text(seg.data["content"])

    @build("image")
    def image(self, seg: MessageSegment):
        return Image(url=seg.data["picURL"])

    @build("at")
    def at(self, seg: MessageSegment):
        if seg.data.get("isAtAll"):
            return AtAll()
        if "atDingtalkIds" in seg.data:
            return At("user", seg.data["atDingtalkIds"][0])
        return
