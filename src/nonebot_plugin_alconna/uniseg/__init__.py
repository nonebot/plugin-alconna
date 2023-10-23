from nonebot.plugin import PluginMetadata

from .segment import At as At
from .segment import File as File
from .segment import Text as Text
from .segment import AtAll as AtAll
from .segment import Audio as Audio
from .segment import Emoji as Emoji
from .segment import Image as Image
from .segment import Other as Other
from .segment import Reply as Reply
from .segment import Video as Video
from .segment import Voice as Voice
from .const import log  # noqa: F401
from .params import UniMsg as UniMsg
from .segment import RefNode as RefNode
from .segment import Segment as Segment
from .segment import Reference as Reference
from .message import UniMessage as UniMessage
from .segment import CustomNode as CustomNode
from .export import SerializeFailed as SerializeFailed
from .fallback import FallbackMessage as FallbackMessage
from .fallback import FallbackSegment as FallbackSegment
from .params import UniversalMessage as UniversalMessage
from .params import UniversalSegment as UniversalSegment

__version__ = "0.30.1"

__plugin_meta__ = PluginMetadata(
    name="Universal Segment 插件",
    description="提供抽象的消息元素，与跨平台接收/发送消息功能的库",
    usage="unimsg: UniMsg",
    homepage="https://github.com/nonebot/plugin-alconna/tree/master/src/nonebot_plugin_alconna/uniseg",
    type="library",
    supported_adapters=None,
    extra={
        "author": "RF-Tar-Railt",
        "priority": 1,
        "version": __version__,
    },
)
