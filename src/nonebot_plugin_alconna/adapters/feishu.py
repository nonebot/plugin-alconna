from nonebot_plugin_alconna.typings import gen_unit
from nonebot_plugin_alconna.analyser import MessageContainer

MessageContainer.config(
    preprocessors={"MessageSegment": lambda x: str(x) if x.type == "text" else None}
)

At = gen_unit("at")
Post = gen_unit("post")
Image = gen_unit("image")
Interactive = gen_unit("interactive")
ShareChat = gen_unit("share_chat")
ShareUser = gen_unit("share_user")
Audio = gen_unit("audio")
Media = gen_unit("media")
File = gen_unit("File")
Sticker = gen_unit("sticker")
