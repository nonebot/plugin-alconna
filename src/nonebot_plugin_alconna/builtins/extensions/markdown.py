import re

from arclet.alconna import Alconna
from arclet.alconna.tools.formatter import MarkdownTextFormatter

from nonebot_plugin_alconna.extension import OutputType
from nonebot_plugin_alconna import Text, Extension, UniMessage


class MarkdownOutputExtension(Extension):
    """
    用于将 Alconna 的自动输出转换为 Markdown 格式

    Example:
        ```python
        from nonebot_plugin_alconna import MsgId, on_alconna
        from nonebot_plugin_alconna.builtins.extensions import MarkdownOutputExtension

        matcher = on_alconna(..., extensions=[MarkdownOutputExtension(escape_dot=...)])
        ```
    """

    @property
    def priority(self) -> int:
        return 16

    @property
    def id(self) -> str:
        return "builtins.extensions.markdown:MarkdownOutputExtension"

    def __init__(self, escape_dot: bool = False):
        """
        Args:
            escape_dot: 是否转义句中的点号（用来避免被识别为 url）
        """
        self.escape_dot = escape_dot

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


__extension__ = MarkdownOutputExtension
