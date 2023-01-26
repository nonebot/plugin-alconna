from nonebot_plugin_alconna.typings import gen_unit
from nonebot_plugin_alconna.analyser import MessageContainer

MessageContainer.config(
    preprocessors={
        "MessageSegment": lambda x: str(x) if x.type == "text" else None,
        "Text": lambda x: str(x)
    }
)

Ark = gen_unit("ark")
Embed = gen_unit("embed")
Emoji = gen_unit("emoji")
Image = gen_unit("attachment")
FileImage = gen_unit("file_image")
MentionUser = gen_unit("mention_user")
MentionChannel = gen_unit("mention_channel")
