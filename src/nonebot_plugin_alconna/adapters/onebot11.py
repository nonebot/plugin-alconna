from nonebot_plugin_alconna.typings import gen_unit
from nonebot_plugin_alconna.analyser import MessageContainer
from nepattern import (
    URL,
    BasePattern,
    PatternModel,
    UnionArg,
)
from nepattern.main import INTEGER
MessageContainer.config(
    preprocessors={"MessageSegment": lambda x: str(x) if x.type == "text" else None}
)

Anonymous = gen_unit("anonymous")
Text = str
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


ImgOrUrl = (
    UnionArg(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=str,
                converter=lambda _, x: x.data['url'],
                alias="img",
                accepts=[Image],
            ),
            URL,
        ]
    )
    @ "img_url"
)
"""
内置类型, 允许传入图片元素(Image)或者链接(URL)，返回链接
"""

AtID = (
    UnionArg(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=int,
                alias="At",
                accepts=[At],
                converter=lambda _, x: int(x.data['qq']),
            ),
            BasePattern(
                r"@(\d+)",
                model=PatternModel.REGEX_CONVERT,
                origin=int,
                alias="@xxx",
                accepts=[str],
            ),
            INTEGER,
        ]
    )
    @ "at_id"
)
"""
内置类型，允许传入提醒元素(At)或者'@xxxx'式样的字符串或者数字, 返回数字
"""
