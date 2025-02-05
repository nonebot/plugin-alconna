from enum import Enum
from typing import Optional
from dataclasses import dataclass

from nonebot.adapters import Bot
from nonebot.adapters import MessageSegment as BaseMessageSegment

from nonebot_plugin_alconna.uniseg.builder import MessageBuilder
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg import Segment, custom_handler, custom_register


class MusicShareKind(str, Enum):
    """音乐分享的来源。"""

    NeteaseCloudMusic = "NeteaseCloudMusic"
    """网易云音乐"""

    QQMusic = "QQMusic"
    """QQ音乐"""

    MiguMusic = "MiguMusic"
    """咪咕音乐"""

    KugouMusic = "KugouMusic"
    """酷狗音乐"""

    KuwoMusic = "KuwoMusic"
    """酷我音乐"""

    Custom = "Custom"
    """自定义音乐来源"""

    @classmethod
    def _missing_(cls, value):
        return MusicShareKind.Custom


@dataclass
class MusicShare(Segment):
    """表示消息中音乐分享消息元素"""

    kind: MusicShareKind
    """音乐分享的来源"""

    id: Optional[str] = None
    """音乐分享的ID"""

    title: Optional[str] = None
    """音乐卡片标题"""

    content: Optional[str] = None
    """音乐卡片内容，例如歌手，专辑信息"""

    url: Optional[str] = None
    """点击卡片跳转的链接"""

    thumbnail: Optional[str] = None
    """音乐图片链接"""

    audio: Optional[str] = None
    """音乐链接"""

    summary: Optional[str] = None
    """音乐摘要/预览信息"""


@custom_register(MusicShare, "music")
def music_build(builder: MessageBuilder, seg: BaseMessageSegment):
    if builder.get_adapter() is SupportAdapter.kritor:
        from nonebot.adapters.kritor.protos.kritor.common import MusicElementMusicPlatform

        kind = {
            MusicElementMusicPlatform.NETEASE: MusicShareKind.NeteaseCloudMusic,
            MusicElementMusicPlatform.QQ: MusicShareKind.QQMusic,
        }.get(seg.data["platform"], MusicShareKind.Custom)
        if "id" in seg.data:
            return MusicShare(kind=kind, id=seg.data["id"])
        data = seg.data["custom"]
        return MusicShare(
            kind=kind,
            url=data["url"],
            title=data["title"],
            content=data["author"],
            thumbnail=data["pic"],
            audio=data["audio"],
        )
    if builder.get_adapter() is SupportAdapter.mirai:
        data = seg.data
        return MusicShare(
            kind=MusicShareKind(data["kind"].value),
            title=data["title"],
            content=data["summary"],
            url=data["jump_url"],
            thumbnail=data["picture_url"],
            audio=data["music_url"],
            summary=data["brief"],
        )
    return None


@custom_handler(MusicShare)
async def music_export(exporter: MessageExporter, seg: MusicShare, bot: Optional[Bot], fallback):
    if exporter.get_adapter() is SupportAdapter.kritor:
        from nonebot.adapters.kritor.message import Music
        from nonebot.adapters.kritor.protos.kritor.common import MusicElementMusicPlatform

        platform = {
            MusicShareKind.NeteaseCloudMusic: MusicElementMusicPlatform.NETEASE,
            MusicShareKind.QQMusic: MusicElementMusicPlatform.QQ,
        }.get(seg.kind, MusicElementMusicPlatform.CUSTOM)

        if seg.id:
            return Music("music", {"platform": platform, "id": seg.id})
        data = {
            "url": seg.url or seg.audio or "",
            "audio": seg.audio or seg.url or "",
            "title": seg.title or "",
            "author": seg.content or seg.summary or "",
            "pic": seg.thumbnail or "",
        }
        return Music(
            "music",
            {
                "platform": platform,
                "custom": data,  # type: ignore
            },
        )

    if exporter.get_adapter() is SupportAdapter.mirai:
        from nonebot.adapters.mirai.message import MessageSegment

        return MessageSegment.music(
            seg.kind.value, seg.title, seg.content, seg.url, seg.thumbnail, seg.audio, seg.summary or "[音乐分享]"
        )

    if exporter.get_adapter() is SupportAdapter.onebot11:
        from nonebot.adapters.onebot.v11.message import MessageSegment

        platform = {
            MusicShareKind.NeteaseCloudMusic: "163",
            MusicShareKind.QQMusic: "qq",
            MusicShareKind.MiguMusic: "migu",
            MusicShareKind.KugouMusic: "kugou",
            MusicShareKind.KuwoMusic: "kuwo",
        }.get(seg.kind, "qq")

        if seg.id:
            return MessageSegment.music(platform, int(seg.id))
        res = MessageSegment.music_custom(
            url=seg.url or seg.audio or "",
            audio=seg.audio or seg.url or "",
            title=seg.title or "",
            content=seg.content or seg.summary or "",
            img_url=seg.thumbnail or "",
        )
        res.data["subtype"] = platform
        return res
    return None
