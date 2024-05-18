from nonebot.adapters.satori.message import At as _At
from nonebot.adapters.satori.message import File as _File
from nonebot.adapters.satori.message import Link as _Link
from nonebot.adapters.satori.message import MessageSegment
from nonebot.adapters.satori.message import Audio as _Audio
from nonebot.adapters.satori.message import Image as _Image
from nonebot.adapters.satori.message import Sharp as _Sharp
from nonebot.adapters.satori.message import Video as _Video
from nonebot.adapters.satori.message import Author as _Author
from nonebot.adapters.satori.message import RenderMessage as _RenderMessage

from nonebot_plugin_alconna.uniseg import Text
from nonebot_plugin_alconna.uniseg import Other
from nonebot_plugin_alconna.uniseg import Reference
from nonebot_plugin_alconna.uniseg import At as UniAt
from nonebot_plugin_alconna.uniseg import File as UniFile
from nonebot_plugin_alconna.uniseg import AtAll as UniAtAll
from nonebot_plugin_alconna.uniseg import Audio as UniAudio
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.uniseg import Reply as UniReply
from nonebot_plugin_alconna.uniseg import Video as UniVideo
from nonebot_plugin_alconna.typings import SegmentPattern, TextSegmentPattern

At = SegmentPattern("at", _At, UniAt, MessageSegment.at, lambda x: x.origin is not None and "id" in x.origin.data)
AtRole = SegmentPattern(
    "at", _At, UniAt, MessageSegment.at_role, lambda x: x.origin is not None and "role" in x.origin.data
)
AtAll = SegmentPattern(
    "at",
    _At,
    UniAtAll,
    MessageSegment.at_all,
    lambda x: x.origin is not None and x.origin.data.get("type") in ("all", "here"),
)
Sharp = SegmentPattern("sharp", _Sharp, UniAt, MessageSegment.sharp)

Image = SegmentPattern("img", _Image, UniImage, MessageSegment.image)
Audio = SegmentPattern("audio", _Audio, UniAudio, MessageSegment.audio)
Video = SegmentPattern("video", _Video, UniVideo, MessageSegment.video)
File = SegmentPattern("file", _File, UniFile, MessageSegment.file)
RenderMessage = SegmentPattern("message", _RenderMessage, Reference, MessageSegment.message)
Quote = SegmentPattern("quote", _RenderMessage, UniReply, MessageSegment.quote)
Author = SegmentPattern("author", _Author, Other, MessageSegment.author)


def link(self, x: Text):
    if x.extract_most_style() == "link":
        if not getattr(x, "_children", []):
            return MessageSegment.link(x.text)
        else:
            return MessageSegment.link(x.text, x._children[0].text)  # type: ignore


Link = TextSegmentPattern("link", _Link, MessageSegment.link, link)
