from nonebot.adapters.wxmp.message import MessageSegment
from nonebot.adapters.wxmp.message import Text as TextSegment
from nonebot.adapters.wxmp.message import Emjoy as EmojiSegment
from nonebot.adapters.wxmp.message import Image as ImageSegment
from nonebot.adapters.wxmp.message import Video as VideoSegment
from nonebot.adapters.wxmp.message import Voice as VoiceSegment
from nonebot.adapters.wxmp.message import Location as LocationSegment
from nonebot.adapters.wxmp.message import Miniprogrampage as MiniProgramSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import Text, Audio, Emoji, Hyper, Image, Other, Video


class WXMPMessageBuilder(MessageBuilder[MessageSegment]):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.wxmp

    @build("text")
    def build_text(self, seg: TextSegment):
        return Text(seg.data["text"])

    @build("image")
    def build_image(self, seg: ImageSegment):
        return Image(id=seg.data["media_id"], url=str(seg.data["file_url"]))

    @build("miniprogrampage")
    def build_miniprogrampage(self, seg: MiniProgramSegment):
        return Hyper("json", content={**seg.data})

    @build("video")
    def build_video(self, seg: VideoSegment):
        return Video(id=seg.data["media_id"])

    @build("voice")
    def build_voice(self, seg: VoiceSegment):
        return Audio(id=seg.data["media_id"])

    @build("location")
    def build_location(self, seg: LocationSegment):
        return Other(seg)

    @build("emjoy")
    def build_emoji(self, seg: EmojiSegment):
        t = seg.data["emjoy"]
        return Emoji(t.value, t.name)
