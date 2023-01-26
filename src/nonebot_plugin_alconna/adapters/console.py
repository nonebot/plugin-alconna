from nonebot_plugin_alconna.typings import gen_unit
from nonebot_plugin_alconna.analyser import MessageContainer

MessageContainer.config(
    preprocessors={"MessageSegment": lambda x: str(x) if x.type == "text" else None}
)

Markdown = gen_unit("markdown")
