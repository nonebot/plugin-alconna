from nonebot_plugin_alconna.typings import gen_unit
from nonebot_plugin_alconna.analyser import MessageContainer


def is_text(seg) -> bool:
    if seg.type == "kmarkdown":
        return seg.data["is_plain_text"]
    else:
        return seg.type == "text"


MessageContainer.config(
    preprocessors={
        "MessageSegment": lambda x: str(x) if is_text(x) else None,
    }
)

Text = str
Image = gen_unit("image")
Video = gen_unit("video")
File = gen_unit("file")
Audio = gen_unit("audio")
KMarkdown = gen_unit("kmarkdown")
Card = gen_unit("card")
