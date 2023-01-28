from nonebot_plugin_alconna.typings import gen_unit
from nonebot_plugin_alconna.analyser import MessageContainer

MessageContainer.config(
    preprocessors={"MessageSegment": lambda x: str(x) if x.type in ("text", "room_at_msg") else None}
)

Card = gen_unit("card")
Link = gen_unit("link")
Image = gen_unit("image")
File = gen_unit("file")
Video = gen_unit("video")
XML = gen_unit("xml")
