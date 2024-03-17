from nonebot.plugin import PluginMetadata

from .segment import At as At
from .segment import File as File
from .segment import Text as Text
from .params import MsgId as MsgId
from .segment import AtAll as AtAll
from .segment import Audio as Audio
from .segment import Emoji as Emoji
from .segment import Hyper as Hyper
from .segment import Image as Image
from .segment import Other as Other
from .segment import Reply as Reply
from .segment import Video as Video
from .segment import Voice as Voice
from .params import UniMsg as UniMsg
from .segment import Custom as Custom
from .tools import get_bot as get_bot
from .exporter import Target as Target
from .message import Receipt as Receipt
from .segment import RefNode as RefNode
from .segment import Segment as Segment
from .constraint import log  # noqa: F401
from .params import MessageId as MessageId
from .params import MsgTarget as MsgTarget
from .segment import Reference as Reference
from .message import UniMessage as UniMessage
from .segment import CustomNode as CustomNode
from .tools import image_fetch as image_fetch
from .tools import reply_fetch as reply_fetch
from .params import MessageTarget as MessageTarget
from .segment import custom_register as custom_register
from .constraint import SupportAdapter as SupportAdapter
from .fallback import FallbackMessage as FallbackMessage
from .fallback import FallbackSegment as FallbackSegment
from .params import UniversalMessage as UniversalMessage
from .params import UniversalSegment as UniversalSegment
from .constraint import SerializeFailed as SerializeFailed
from .segment import apply_media_to_url as apply_media_to_url
from .constraint import SupportAdapterModule as SupportAdapterModule

__version__ = "0.41.0"

__plugin_meta__ = PluginMetadata(
    name="Universal Segment 插件",
    description="提供抽象的消息元素，与跨平台接收/发送消息功能的库",
    usage="unimsg: UniMsg",
    homepage="https://github.com/nonebot/plugin-alconna/tree/master/src/nonebot_plugin_alconna/uniseg",
    type="library",
    supported_adapters=set(SupportAdapterModule.__members__.values()),
    extra={
        "author": "RF-Tar-Railt",
        "priority": 1,
        "version": __version__,
    },
)


def patch_saa():
    from .utils import saa  # noqa: F401


def apply_filehost():
    from .utils import filehost  # noqa: F401


reply_handle = reply_fetch  # backward compatibility
