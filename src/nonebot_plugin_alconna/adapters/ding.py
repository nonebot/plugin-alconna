from nonebot_plugin_alconna.typings import gen_unit
from nonebot_plugin_alconna.analyser import MessageContainer

MessageContainer.config(
    preprocessors={"MessageSegment": lambda x: str(x) if x.type == "text" else None}
)

AtAll = gen_unit("at", lambda x: "isAtAll" in x.data)
AtMobiles = gen_unit("at", lambda x: "atMobiles" in x.data)
AtDingtalkIds = gen_unit("at", lambda x: "atDingtalkIds" in x.data)
Image = gen_unit("image")
Extension = gen_unit("extension")
Code = gen_unit("code")
Markdown = gen_unit("markdown")
ActionCardSingleBtn = gen_unit("actionCard", lambda x: "singleTitle" in x.data)
ActionCardMultiBtns = gen_unit("actionCard", lambda x: "btns" in x.data)
FeedCard = gen_unit("feedCard")
Raw = gen_unit("raw")
