"""通用标注, 无法用于创建 MS对象"""
from nonebot_plugin_alconna.typings import gen_unit
from nonebot.internal.adapter.message import MessageSegment
from nepattern import create_local_patterns
from dataclasses import dataclass, field
from typing import Optional


Text = str

@dataclass
class Segment:
    """基类标注"""
    origin: MessageSegment


@dataclass
class At(Segment):
    """At对象, 表示一类提醒某用户的元素"""
    target: str

@dataclass
class Media(Segment):
    url: Optional[str] = field(default=None)
    id: Optional[str] = field(default=None)

@dataclass
class Image(Media):
    """Image对象, 表示一类图片元素"""

@dataclass
class Audio(Media):
    """Audio对象, 表示一类音频元素"""

@dataclass
class Voice(Media):
    """Voice对象, 表示一类语音元素"""

@dataclass
class Video(Media):
    """Video对象, 表示一类视频元素"""

@dataclass
class File(Segment):
    """File对象, 表示一类文件元素"""
    id: str
    name: Optional[str] = field(default=None)


_At = gen_unit(
    At,
    {
        "at": lambda seg: At(seg, str(seg.data.get("qq", seg.data.get("user_id")))),
        "mention": lambda seg: At(seg, seg.data.get("user_id", seg.data.get("text"))),
        "mention_user": lambda seg: At(seg, str(seg.data["user_id"])),
        "At": lambda seg: At(seg, str(seg, seg.data["target"])),
        "kmarkdown": lambda seg: (
            seg.startswith("(met)") and
            ((end := seg.find("(met)", 5)) != -1 and seg[5: end] not in ("here", "all") and At(seg, seg[5: end]))
        ),
    }
)
"""
at: ob11, feishu
mention: ob12, tg
mention_user: qqguild
At: mirai
kmarkdown: kook
"""


def _handle_image(seg: MessageSegment):
    if "file_id" in seg.data:  # ob12
        return Image(seg, id=seg.data["file_id"])
    if "image_key" in seg.data:  # feishu
        return Image(seg, url=seg.data["image_key"])
    if "file_key" in seg.data:  # kook
        return Image(seg, url=seg.data["file_key"])
    if "url" in seg.data:  # ob11, qqguild
        return Image(seg, url=seg.data["url"])
    if "msgData" in seg.data:  # minecraft
        return Image(seg, url=seg.data["msgData"])
    if "file_path" in seg.data:  # ntchat
        return Image(seg, id=seg.data["file_path"])
    if "picURL" in seg.data:  # ding
        return Image(seg, url=seg.data["picURL"])



_Image = gen_unit(
    Image,
    {
        "image": _handle_image,
        "photo": lambda seg: Image(seg, id=seg.data["file_id"]),
        "Image": lambda seg: Image(seg, seg.data["url"], seg.data["imageId"]),
    }
)


def _handle_video(seg: MessageSegment):
    if "file_id" in seg.data:  # ob12, telegram
        return Video(seg, id=seg.data["file_id"])
    if "file" in seg.data:  # ob11
        return Video(seg, url=seg.data["file"])
    if "file_key" in seg.data:  # kook
        return Video(seg, url=seg.data["file_key"])
    if "msgData" in seg.data:  # minecraft
        return Video(seg, url=seg.data["msgData"])
    if "file_path" in seg.data:  # ntchat
        return Video(seg, id=seg.data["file_path"])


_Video = gen_unit(
    Video,
    {
        "video": lambda seg: Video(seg, seg.data["url"], seg.data["videoId"]),
        "animation": lambda seg: Video(seg, id=seg.data["file_id"]),
    }
)


def _handle_voice(seg: MessageSegment):
    if "file_id" in seg.data:  # ob12, telegram
        return Voice(seg, id=seg.data["file_id"])
    if "file_key" in seg.data:  # kook
        return Voice(seg, url=seg.data["file_key"])
    if "file_path" in seg.data:  # ntchat
        return Voice(seg, id=seg.data["file_path"])

_Voice = gen_unit(
    Voice,
    {
        "voice": _handle_voice,
        "record": lambda seg: Voice(seg, seg.data["url"]),
        "Voice": lambda seg: Voice(seg, seg.data["url"], seg.data["voiceId"]),
    }
)

def _handle_audio(seg: MessageSegment):
    if "file_id" in seg.data:  # ob12, telegram
        return Audio(seg, id=seg.data["file_id"])
    if "file_key" in seg.data:  # kook, feishu
        return Audio(seg, url=seg.data["file_key"])
    if "file_path" in seg.data:  # ntchat
        return Audio(seg, id=seg.data["file_path"])

_Audio = gen_unit(
    Audio,
    {
        "audio": _handle_audio,
    }
)


def _handle_file(seg: MessageSegment):
    if "file_id" in seg.data:  # ob12
        return File(seg, id=seg.data["file_id"])
    if "file_key" in seg.data:  # feishu, kook
        return File(seg, id=seg.data["file_key"], name=seg.data.get("file_name", seg.data.get("title")))
    if "file_path" in seg.data:  # ntchat
        return File(seg, id=seg.data["file_path"])

_File = gen_unit(
    File,
    {
        "file": _handle_file,
        "document": lambda seg: File(seg, seg.data["file_id"], seg.data["file_name"]),
        "File": lambda seg: File(seg, seg.data["id"], seg.data["name"]),
    }
)

env = create_local_patterns("nonebot")
env.sets([_At, _Image, _Video, _Voice, _Audio, _File])