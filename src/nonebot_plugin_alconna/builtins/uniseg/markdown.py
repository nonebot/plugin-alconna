from dataclasses import dataclass
from typing import Optional, cast

from nonebot.adapters import Bot
from nepattern import BasePattern, UnionPattern, local_patterns
from nonebot.adapters import MessageSegment as BaseMessageSegment

from nonebot_plugin_alconna.typings import Style
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg import Text, Segment, custom_handler, custom_register


@dataclass
class Markdown(Segment):
    content: Optional[str] = None
    template_id: Optional[str] = None
    params: Optional[dict[str, list[str]]] = None


@custom_register(Markdown, "markdown")
def mdbuild(builder: MessageBuilder, seg: BaseMessageSegment):
    if builder.get_adapter() is SupportAdapter.qq:
        from nonebot.adapters.qq.message import Markdown as MarkdownSegment

        seg = cast(MarkdownSegment, seg)
        return Markdown(
            template_id=seg.data["markdown"].custom_template_id,
            params=(
                {param.key: param.values for param in seg.data["markdown"].params}  # type: ignore
                if seg.data["markdown"].params
                else None
            ),
        )
    return None


@custom_handler(Markdown)
async def music_export(exporter: MessageExporter, seg: Markdown, bot: Optional[Bot], fallback):
    if exporter.get_adapter() is SupportAdapter.qq and seg.template_id:
        from nonebot.adapters.qq.message import MessageSegment
        from nonebot.adapters.qq.models import MessageMarkdown, MessageMarkdownParams

        if seg.params:
            params = [MessageMarkdownParams(key=k, values=v) for k, v in seg.params.items()]
        else:
            params = None
        md = MessageMarkdown(custom_template_id=seg.template_id, params=params)
        return MessageSegment.markdown(md)

    if seg.content:
        return (await exporter.export([Text(seg.content).markdown()], bot, fallback))[0]
    return None


local_patterns()[Markdown] = UnionPattern([Style("markdown"), BasePattern.of(Markdown)])
