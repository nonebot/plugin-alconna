import re
from collections.abc import Awaitable
from typing import Callable, Optional

from arclet.alconna import Alconna
from nonebot.internal.adapter import Bot, Event
from arclet.alconna.tools.formatter import MarkdownTextFormatter

from nonebot_plugin_alconna.extension import TM, OutputType
from nonebot_plugin_alconna import Text, Image, Extension, UniMessage


class MarkdownOutputExtension(Extension):
    """
    用于将 Alconna 的自动输出转+换为 Markdown 格式

    Example:
        >>> from nonebot_plugin_alconna import MsgId, on_alconna
        >>> from nonebot_plugin_alconna.builtins.extensions import MarkdownOutputExtension
        >>>
        >>> matcher = on_alconna("...", extensions=[MarkdownOutputExtension(escape_dot=..., text_to_image=...)])
    """

    @property
    def priority(self) -> int:
        return 16

    @property
    def id(self) -> str:
        return "builtins.extensions.markdown:MarkdownOutputExtension"

    def __init__(self, escape_dot: bool = False, text_to_image: Optional[Callable[[str], Awaitable[Image]]] = None):
        """
        Args:
            escape_dot: 是否转义句中的点号（用来避免被识别为 url）
            text_to_image: 文字转图片的函数
        """
        self.escape_dot = escape_dot
        self.text_to_image = text_to_image

    def post_init(self, alc: Alconna) -> None:
        alc.formatter = MarkdownTextFormatter().add(alc)

    async def output_converter(self, output_type: OutputType, content: str):
        if output_type in ("shortcut", "error"):
            if self.escape_dot:
                content = re.sub(r"\w\.\w", lambda mat: mat[0].replace(".", ". "), content)
            msg = UniMessage.text(content)
        elif output_type == "completion":
            content = (
                content.replace("\n\n", "\n")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&#123;", "{")
                .replace("&#125;", "}")
            )
            if self.escape_dot:
                content = re.sub(r"\w\.\w", lambda mat: mat[0].replace(".", ". "), content)
            msg = UniMessage.text(content)
        else:
            if not content.startswith("#"):
                content = f"# {content}"
                content = (
                    content.replace("\n\n", "\n")
                    .replace("\n", "\n\n")
                    .replace("#", "##")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
            if self.escape_dot:
                content = re.sub(r"\w\.\w", lambda mat: mat[0].replace(".", ". "), content)
            msg = UniMessage([Text(content).mark(0, len(content), "markdown")])
        return msg

    async def send_wrapper(self, bot: Bot, event: Event, send: TM) -> TM:
        if self.text_to_image and isinstance(send, UniMessage) and send.has(Text):
            text = send[Text, 0]
            if text.extract_most_style() == "markdown":
                img = await self.text_to_image(text.text)
                index = send.index(text)
                send[index] = img
        return send


__extension__ = MarkdownOutputExtension
