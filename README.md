<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://v2.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>

<div align="center">

# NoneBot Plugin Alconna

_✨ Alconna Usage For NoneBot2 ✨_

</div>

<p align="center">
  <a href="https://raw.githubusercontent.com/ArcletProject/nonebot-plugin-alconna/master/LICENSE">
    <img src="https://img.shields.io/github/license/ArcletProject/nonebot_plugin_alconna.svg" alt="license">
  </a>
  <a href="https://pypi.python.org/pypi/nonebot-plugin-alconna">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-alconna.svg" alt="pypi">
  </a>
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">
</p>

## 使用方法

### Matcher 与 依赖注入
```python
from nonebot_plugin_alconna import on_alconna, Match, AlconnaMatch
from arclet.alconna import Alconna, Args

test = on_alconna(Alconna("test", Args["foo", int]["bar", bool]))


@test.handle()
async def handle_echo(foo: Match[int] = AlconnaMatch("foo")):
    if foo.available:    
        await test.send(f"foo={foo.result}")
```

### MessageSegment Mark

```python
from nonebot_plugin_alconna.adapters.onebot import Mention
from nonebot.adapters.onebot.v12 import Message, MessageSegment
from arclet.alconna import Alconna, Args

msg = Message(["Hello!", MessageSegment.mention("123")])
print(msg)  # Hello![mention:user_id=123]

alc = Alconna("Hello!", Args["target", Mention])
res = alc.parse(msg)
assert res.matched
assert res.target.data['user_id'] == '123'
```

## 提供了 MessageSegment Mark 的协议:

| 协议名称                                                   | 状态  |
|--------------------------------------------------------|-----|
| [OneBot 协议](https://onebot.dev/)                       | ✅   |
| [Telegram](https://core.telegram.org/bots/api)         | ✅   |
| [飞书](https://open.feishu.cn/document/home/index)       | ✅   |
| [GitHub](https://docs.github.com/en/developers/apps)   | ✅   |
| [QQ 频道](https://bot.q.qq.com/wiki/)                    | ✅   |
| [钉钉](https://open.dingtalk.com/document/)              | ✅   |
| [Console](https://github.com/nonebot/adapter-console)  | ✅   |
| [开黑啦](https://developer.kookapp.cn/)                   | 🚧  |
| [Mirai](https://docs.mirai.mamoe.net/mirai-api-http/)  | 🚧    |
| [Ntchat](https://github.com/JustUndertaker/adapter-ntchat) | 🚧    |
| [MineCraft (Spigot)](https://github.com/17TheWord/nonebot-adapter-spigot) | 🚧    |
| [BiliBili Live](https://github.com/wwweww/adapter-bilibili) | 🚧    |
