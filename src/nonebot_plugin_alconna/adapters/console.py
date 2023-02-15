from nonebot_plugin_alconna.typings import gen_unit
from nonebot_plugin_alconna.analyser import MessageContainer

MessageContainer.config(
    preprocessors={
        "MessageSegment": lambda x: x.data["text"] if x.type == "text" else None,
        "Text": lambda x: x.data["text"],
        "Emoji": lambda x: None,
        "Markup": lambda x: None,
        "Markdown": lambda x: None
    }
)

Emoje = gen_unit("emoji")
Markup = gen_unit("markup")
Markdown = gen_unit("markdown")
Text = str
