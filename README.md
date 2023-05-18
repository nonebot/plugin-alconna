<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://v2.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>

<div align="center">

# NoneBot Plugin Alconna

_✨ Alconna Usage For NoneBot2 ✨_

</div>

<p align="center">
  <a href="https://raw.githubusercontent.com/ArcletProject/nonebot-plugin-alconna/master/LICENSE">
    <img src="https://img.shields.io/github/license/ArcletProject/nonebot-plugin-alconna.svg" alt="license">
  </a>
  <a href="https://pypi.python.org/pypi/nonebot-plugin-alconna">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-alconna.svg" alt="pypi">
  </a>
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">
</p>

该插件提供了 [Alconna](https://github.com/ArcletProject/Alconna) 的 [Nonebot2](https://github.com/nonebot/nonebot2) 适配版本与工具

## 特性

- 完整的 Alconna 特性支持
- 基本的 rule, matcher 与 依赖注入
- 自动回复命令帮助信息 (help, shortcut, completion) 选项
- 现有全部协议的 Segment 标注
- match_value, match_path 等检查函数
- 补全会话支持

## 讨论

QQ 交流群: [链接](https://jq.qq.com/?_wv=1027&k=PUPOnCSH)


## 使用方法

### 消息解析

```python
from nonebot.adapters.onebot.v12 import Message, MessageSegment
from arclet.alconna import Alconna, Option, Args

msg = Message("Hello! --foo 123")
img = MessageSegment.image("1.png")
print(msg)

alc = Alconna("Hello!", Option("--foo", Args["foo", int]))
res = alc.parse(msg)
assert res.matched
assert res.query("foo.foo") == 123
assert not alc.parse(Message(["Hello!", img])).matched
```

### MessageSegment 标注

特定适配器:

```python
from nonebot_plugin_alconna.adapters.onebot12 import Mention
from nonebot.adapters.onebot.v12 import Message
from arclet.alconna import Alconna, Args

msg = Message(["Hello!", Mention("123")])
print(msg)  # Hello![mention:user_id=123]

alc = Alconna("Hello!", Args["target", Mention])
res = alc.parse(msg)
assert res.matched
assert res.query("target").data['user_id'] == '123'
```

通用标注:

```python
from nonebot.adapters.onebot.v12 import Message as Ob12M, MessageSegment as Ob12MS
from nonebot.adapters.onebot.v11 import Message as Ob11M, MessageSegment as Ob11MS
from nonebot_plugin_alconna.adapters import At
from arclet.alconna import Alconna, Args

msg1 = Ob12M(["Hello!", Ob12MS.mention("123")])
print(msg1)  # Hello![mention:user_id=123]
msg2 = Ob11M(["Hello!", Ob11MS.at(123)])
print(msg2)  # Hello![CQ:at,qq=123]

alc = Alconna("Hello!", Args["target", At])
res1 = alc.parse(msg1)
assert res1.matched
assert res1.query("target").data['user_id'] == '123'

res2 = alc.parse(msg2)
assert res2.matched
assert res2.query("target").data['qq'] == 123
```

### Matcher 与 依赖注入
```python
...
from nonebot import require
require("nonebot_plugin_alconna")
...

from nonebot_plugin_alconna import (
    on_alconna, 
    Match,
    Query,
    AlconnaMatch, 
    AlconnaQuery,
    AlcMatches,
    AlcResult
)
from arclet.alconna import Alconna, Args, Option

test = on_alconna(
    Alconna(
        "test",
        Option("foo", Args["bar", int]),
        Option("baz", Args["qux", bool, False])
    ),
    auto_send_output=True
)


@test.handle()
async def handle_test1(result: AlcResult):
    await test.send(f"matched: {result.matched}")
    await test.send(f"maybe output: {result.output}")

@test.handle()
async def handle_test2(result: AlcMatches):
    await test.send(f"head result: {result.header_result}")
    await test.send(f"args: {result.all_matched_args}")

@test.handle()
async def handle_test3(bar: Match[int] = AlconnaMatch("bar")):
    if bar.available:    
        await test.send(f"foo={bar.result}")

@test.handle()
async def handle_test4(qux: Query[bool] = AlconnaQuery("baz.qux", False)):
    if qux.available:
        await test.send(f"baz.qux={qux.result}")
```

### 条件控制

```python
...
from nonebot import require
require("nonebot_plugin_alconna")
...

from arclet.alconna import Alconna, Subcommand, Option, Args
from nonebot_plugin_alconna import assign, on_alconna, AlconnaResult, CommandResult, Check

pip = Alconna(
    "pip",
    Subcommand(
        "install", 
        Args["pak", str],
        Option("--upgrade"),
        Option("--force-reinstall")
    ),
    Subcommand(
        "list",
        Option("--out-dated")
    )
)

pip_cmd = on_alconna(pip)

@pip_cmd.handle([Check(assign("install.pak", "pip"))])
async def update(arp: CommandResult = AlconnaResult()):
    ...

@pip_cmd.handle([Check(assign("list"))])
async def list_(arp: CommandResult = AlconnaResult()):
    ...

@pip_cmd.handle([Check(assign("install"))])
async def install(arp: CommandResult = AlconnaResult()):
    ...
```


### Duplication

```python
...
from nonebot import require
require("nonebot_plugin_alconna")
...

from nonebot_plugin_alconna import (
    on_alconna, 
    AlconnaDuplication
)
from arclet.alconna import Alconna, Args, Duplication, Option, OptionStub

test = on_alconna(
    Alconna(
        "test",
        Option("foo", Args["bar", int]),
        Option("baz", Args["qux", bool, False])
    ),
    auto_send_output=True
)

class MyResult(Duplication):
    bar: int
    qux: bool
    foo: OptionStub

@test.handle()
async def handle_test1(result: MyResult = AlconnaDuplication(MyResult)):
    await test.send(f"matched: bar={result.bar}, qux={result.qux}")
    await test.send(f"options: foo={result.foo.origin}")

```

## 配置

目前配置项有：

- ALCONNA_AUTO_SEND_OUTPUT : 是否全局启用输出信息自动发送
- ALCONNA_USE_COMMAND_START : 是否将 COMMAND_START 作为全局命令前缀
- ALCONNA_AUTO_COMPLETION: 是否全局启用补全会话功能

## 参数解释

```python
def on_alconna(
    command: Alconna | str,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = False,
    output_converter: Callable[[OutputType, str], Message | Awaitable[Message]] | None = None,
    aliases: set[str | tuple[str, ...]] | None = None,
    comp_config: CompConfig | None = None,
    **kwargs,
) -> type[Matcher]:
```

- `command`: Alconna 命令
- `skip_for_unmatch`: 是否在命令不匹配时跳过该响应
- `auto_send_output`: 是否自动发送输出信息并跳过响应
- `output_converter`: 输出信息字符串转换为 Message 方法
- `aliases`: 命令别名, 作用类似于 `on_command`
- `comp_config`: 补全会话配置, 不传入则不启用补全会话

## 提供了 MessageSegment标注 的协议:

| 协议名称                                                                | 路径                                   |
|---------------------------------------------------------------------|--------------------------------------|
| [OneBot 协议](https://onebot.dev/)                                    | adapters.onebot11, adapters.onebot12 |
| [Telegram](https://core.telegram.org/bots/api)                      | adapters.telegram                    |
| [飞书](https://open.feishu.cn/document/home/index)                    | adapters.feishu                      |
| [GitHub](https://docs.github.com/en/developers/apps)                | adapters.github                      |
| [QQ 频道](https://bot.q.qq.com/wiki/)                                 | adapters.qqguild                     |
| [钉钉](https://open.dingtalk.com/document/)                           | adapters.ding                        |
| [Console](https://github.com/nonebot/adapter-console)               | adapters.console                     |
| [开黑啦](https://developer.kookapp.cn/)                                | adapters.kook                        |
| [Mirai](https://docs.mirai.mamoe.net/mirai-api-http/)               | adapters.mirai                       |
| [Ntchat](https://github.com/JustUndertaker/adapter-ntchat)          | adapters.ntchat                      |
| [MineCraft](https://github.com/17TheWord/nonebot-adapter-minecraft) | adapters.minecraft                   |
| [BiliBili Live](https://github.com/wwweww/adapter-bilibili)         | adapters.bilibili                    |




## 体验

[demo bot](./src/test/plugins/demo.py)
