from nonebot_plugin_alconna.typings import gen_unit
from nonebot_plugin_alconna.analyser import MessageContainer

MessageContainer.config(
    preprocessors={"MessageSegment": lambda x: str(x) if x.type == "text" else None}
)

# V11
Anonymous = gen_unit("anonymous")
At = gen_unit("at")
Contact = gen_unit("contact")
Dice = gen_unit("dice")
Face = gen_unit("face")
Forward = gen_unit("forward")
Image = gen_unit("image")
Json = gen_unit("json")
Location = gen_unit("location")
Music = gen_unit("music")
Node = gen_unit("node")
Poke = gen_unit("poke")
Record = gen_unit("record")
Reply = gen_unit("reply")
RPS = gen_unit("rps")
Shake = gen_unit("shake")
Share = gen_unit("share")
Video = gen_unit("video")
Xml = gen_unit("xml")

# V12

Mention = gen_unit("mention")
MentionAll = gen_unit("mention_all")
Audio = gen_unit("audio")
Voice = gen_unit("voice")
File = gen_unit("file")
