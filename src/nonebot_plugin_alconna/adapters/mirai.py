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
    preprocessors={"MessageSegment": lambda x: str(x) if x.type == "Plain" else None}
)

Source = gen_unit("Source")
Quote = gen_unit("Quote")
Plain = str
At = gen_unit("At")
AtAll = gen_unit("AtAll")
Face = gen_unit("Face")
Image = gen_unit("Image")
FlashImage = gen_unit("FlashImage")
Voice = gen_unit("Voice")
Xml = gen_unit("Xml")
Json = gen_unit("Json")
App = gen_unit("App")
Dice = gen_unit("Dice")
Poke = gen_unit("Poke")
MarketFace = gen_unit("MarketFace")
MusicShare = gen_unit("MusicShare")
Forward = gen_unit("Forward")
File = gen_unit("File")
MiraiCode = gen_unit("MiraiCode")

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
                converter=lambda _, x: int(x.data['target']),
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
