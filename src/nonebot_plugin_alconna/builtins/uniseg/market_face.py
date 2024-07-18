from typing import Optional
from dataclasses import dataclass

from tarina import lang
from nonebot.adapters import Bot
from nonebot.adapters import MessageSegment as BaseMessageSegment

from nonebot_plugin_alconna.uniseg.builder import MessageBuilder
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter
from nonebot_plugin_alconna.uniseg import Segment, custom_handler, custom_register
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter, SerializeFailed


@dataclass
class MarketFace(Segment):
    """MarketFace对象, 专门表示 QQ 中的商城表情"""

    id: str  # alias: emoji_id
    tab_id: Optional[str] = None  # alias: package_id
    key: Optional[str] = None
    summary: Optional[str] = None  # alias: face_name


@custom_register(MarketFace, "market_face")
def mfbuild(builder: MessageBuilder, seg: BaseMessageSegment):
    if builder.get_adapter() is SupportAdapter.kritor:
        return MarketFace(id=seg.data["id"])
    elif builder.get_adapter() is SupportAdapter.red:
        return MarketFace(
            id=str(seg.data["emoji_id"]),
            tab_id=hex(seg.data["package_id"]),
            key=seg.data.get("key"),
            summary=seg.data.get("face_name"),
        )
    elif builder.get_adapter() is SupportAdapter.mirai_official:
        return MarketFace(
            id=str(seg.data["id"]),
            summary=seg.data["name"],
        )


@custom_register(MarketFace, "mface")
def mfbuild_ob11(builder: MessageBuilder, seg: BaseMessageSegment):
    return MarketFace(
        id=str(seg.data["emoji_id"]),
        tab_id=hex(seg.data["emoji_package_id"]),
        key=seg.data.get("key"),
        summary=seg.data.get("summary"),
    )


@custom_register(MarketFace, "MarketFace")
def mfbuild_mirai_community(builder: MessageBuilder, seg: BaseMessageSegment):
    return MarketFace(
        id=str(seg.data["faceId"]),
        summary=seg.data["name"],
    )


@custom_register(MarketFace, "chronocat:marketface")
def mfbuild_chronocat(builder: MessageBuilder, seg: BaseMessageSegment):
    from nonebot.adapters.satori.message import Custom as CustomSegment

    if not isinstance(seg, CustomSegment):
        raise ValueError("MarketFace can only be built from Satori Message")
    return MarketFace(
        id=seg.data["faceId"],
        tab_id=seg.data["tabId"],
        key=seg.data["key"],
    )(*builder.generate(seg.children))


@custom_handler(MarketFace)
async def mfexport(exporter: MessageExporter, seg: MarketFace, bot: Optional[Bot], fallback):
    if exporter.get_adapter() is SupportAdapter.satori:
        from nonebot.adapters.satori import MessageSegment

        if not seg.tab_id or not seg.key:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="market_face", seg=seg))

        return MessageSegment(
            "chronocat:marketface",
            {
                "faceId": seg.id,
                "tabId": seg.tab_id,
                "key": seg.key,
            },
        )(
            await exporter.export(seg.children, bot, fallback)
        )  # type: ignore

    if exporter.get_adapter() is SupportAdapter.red:
        raise NotImplementedError

    if exporter.get_adapter() is SupportAdapter.kritor:
        from nonebot.adapters.kritor.message import MessageSegment

        return MessageSegment.market_face(seg.id)

    if exporter.get_adapter() is SupportAdapter.mirai_official:
        from nonebot.adapters.mirai.message import MessageSegment

        return MessageSegment.market_face(int(seg.id), seg.summary)

    if exporter.get_adapter() is SupportAdapter.mirai_community:
        from nonebot.adapters.mirai2.message import MessageSegment

        return MessageSegment.market_face(int(seg.id), seg.summary or "商城表情")

    if exporter.get_adapter() is SupportAdapter.onebot11:
        from nonebot.adapters.onebot.v11.message import MessageSegment

        if not seg.tab_id:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="market_face", seg=seg))

        if not seg.key:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="market_face", seg=seg))

        return MessageSegment(
            "mface",
            {
                "emoji_id": int(seg.id),
                "emoji_package_id": int(seg.tab_id, 16),
                "key": seg.key,
                "summary": seg.summary,
            },
        )
