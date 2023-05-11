"""通用标注, 无法用于创建 MS对象"""
from nonebot_plugin_alconna.typings import gen_unit

Text = str
At = gen_unit("at", {"at", "mention", "mention_user"})
Image = gen_unit("image", {"image", "attachment"})
Audio = gen_unit("audio", {"audio"})
Voice = gen_unit("voice", {"voice", "record"})
File = gen_unit("file", {"file"})
Video = gen_unit("video", {"video"})
