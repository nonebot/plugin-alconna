<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://v2.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>

<div align="center">

# NoneBot Plugin Alconna

_✨ Alconna Usage For NoneBot2 ✨_

</div>

<p align="center">
  <a href="https://raw.githubusercontent.com/nonebot/plugin-alconna/master/LICENSE">
    <img src="https://img.shields.io/github/license/nonebot/plugin-alconna.svg" alt="license">
  </a>
  <a href="https://pypi.python.org/pypi/nonebot-plugin-alconna">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-alconna.svg" alt="pypi">
  </a>
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">
</p>

该插件提供了 [Alconna](https://github.com/ArcletProject/Alconna) 的 [NoneBot2](https://github.com/nonebot/nonebot2) 适配版本与工具

## 特性

- 完整的 Alconna 特性支持
- 基本的 rule, matcher 与 依赖注入
- 自动回复命令帮助信息 (help, shortcut, completion) 选项
- 现有全部协议的 Segment 标注
- match_value, match_path 等检查函数
- 补全会话支持
- 跨平台的接收与发送消息

## 讨论

QQ 交流群: [链接](https://jq.qq.com/?_wv=1027&k=PUPOnCSH)


## 使用方法

NoneBot 文档: [📖这里](https://nonebot.dev/docs/next/best-practice/alconna/)
仓库内介绍: [📦这里](/docs.md)

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
from nonebot.adapters.onebot.v12 import Message as Ob12Msg, MessageSegment as Ob12MS
from nonebot.adapters.onebot.v11 import Message as Ob11Msg, MessageSegment as Ob11MS
from nonebot_plugin_alconna import At
from arclet.alconna import Alconna, Args

msg1 = Ob12Msg(["Hello!", Ob12MS.mention("123")]) # Hello![mention:user_id=123]
msg2 = Ob11Msg(["Hello!", Ob11MS.at(123)]) # Hello![CQ:at,qq=123]


alc = Alconna("Hello!", Args["target", At])
res1 = alc.parse(msg1)
assert res1.matched
target = res1.query("target")
assert isinstance(target, At)
assert target.target == '123'

res2 = alc.parse(msg2)
assert res2.matched
target = res2.query("target")
assert isinstance(target, At)
assert target.target == '123'
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
from nonebot_plugin_alconna import on_alconna, AlconnaResult, CommandResult

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

@pip_cmd.assign("install.pak", "pip")
async def update(arp: CommandResult = AlconnaResult()):
    ...

@pip_cmd.assign("list")
async def list_(arp: CommandResult = AlconnaResult()):
    ...

install_cmd = pip_cmd.dispatch("install")

@install_cmd.handle()
async def install(arp: CommandResult = AlconnaResult()):
    ...

@install_cmd.assign("install.pak", "nonebot")
async def nonebot(arp: CommandResult = AlconnaResult()):
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
- ALCONNA_USE_ORIGIN: 是否全局使用原始消息 (即未经过 to_me 等处理的)
- ALCONNA_USE_PARAM: 是否使用特制的 Param 提供更好的依赖注入
- ALCONNA_USE_CMD_SEP: 是否将 COMMAND_SEP 作为全局命令分隔符
- ALCONNA_GLOBAL_EXTENSIONS: 全局加载的扩展, 路径以 . 分隔, 如 foo.bar.baz:DemoExtension

## 参数解释

```python
def on_alconna(
    command: Alconna | str,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = False,
    aliases: set[str | tuple[str, ...]] | None = None,
    comp_config: CompConfig | None = None,
    extensions: list[type[Extension] | Extension] | None = None,
    exclude_ext: list[type[Extension] | str] | None = None,
    use_origin: bool = False,
    use_cmd_start: bool = False,
    use_cmd_sep: bool = False,
    **kwargs,
) -> type[AlconnaMatcher]:
```

- `command`: Alconna 命令
- `skip_for_unmatch`: 是否在命令不匹配时跳过该响应
- `auto_send_output`: 是否自动发送输出信息并跳过响应
- `aliases`: 命令别名, 作用类似于 `on_command`
- `comp_config`: 补全会话配置, 不传入则不启用补全会话
- `extensions`: 需要加载的匹配扩展, 可以是扩展类或扩展实例
- `exclude_ext`: 需要排除的匹配扩展, 可以是扩展类或扩展的id
- `use_origin`: 是否使用未经 to_me 等处理过的消息
- `use_cmd_start`: 是否使用 COMMAND_START 作为命令前缀
- `use_cmd_sep`: 是否使用 COMMAND_SEP 作为命令分隔符

## 提供了 MessageSegment标注 的协议:

| 协议名称                                                                | 路径                                   |
|---------------------------------------------------------------------|--------------------------------------|
| [OneBot 协议](https://onebot.dev/)                                    | adapters.onebot11, adapters.onebot12 |
| [Telegram](https://core.telegram.org/bots/api)                      | adapters.telegram                    |
| [飞书](https://open.feishu.cn/document/home/index)                    | adapters.feishu                      |
| [GitHub](https://docs.github.com/en/developers/apps)                | adapters.github                      |
| [QQ bot](https://github.com/nonebot/adapter-qq)                     | adapters.qq                          |
| [QQ 频道bot](https://bot.q.qq.com/wiki/)                              | adapters.qqguild                     |
| [钉钉](https://open.dingtalk.com/document/)                           | adapters.ding                        |
| [Console](https://github.com/nonebot/adapter-console)               | adapters.console                     |
| [开黑啦](https://developer.kookapp.cn/)                                | adapters.kook                        |
| [Mirai](https://docs.mirai.mamoe.net/mirai-api-http/)               | adapters.mirai                       |
| [Ntchat](https://github.com/JustUndertaker/adapter-ntchat)          | adapters.ntchat                      |
| [MineCraft](https://github.com/17TheWord/nonebot-adapter-minecraft) | adapters.minecraft                   |
| [BiliBili Live](https://github.com/wwweww/adapter-bilibili)         | adapters.bilibili                    |
| [Walle-Q](https://github.com/onebot-walle/nonebot_adapter_walleq)   | adapters.onebot12                    |
| [Villa](https://github.com/CMHopeSunshine/nonebot-adapter-villa)    | adapters.villa                       |
| [Discord](https://github.com/nonebot/adapter-discord)               | adapters.discord                     |
| [Red 协议](https://github.com/nonebot/adapter-red)                    | adapters.red                         |
| [Satori](https://github.com/nonebot/adapter-satori)                 | adapters.satori                      |
| [Dodo IM](https://github.com/nonebot/adapter-dodo)                  | adapters.dodo                        |


## 便捷装饰器

`funcommand` 装饰器用于将一个接受任意参数，返回 `str` 或 `Message` 或 `MessageSegment` 的函数转换为命令响应器。

```python
from nonebot_plugin_alconna import funcommand

@funcommand()
async def echo(msg: str):
    return msg
```

## 跨平台消息

```python
from nonebot_plugin_alconna import UniMessage, on_alconna

test = on_alconna("test")

@test.handle()
async def handle_test():
    await test.send(UniMessage.image(path="path/to/img"))

@test.got("foo", prompt=UniMessage.template("{:Reply($message_id)}请输入图片"))
async def handle_foo():
    await test.send("图片已收到")
```

## 体验

[demo bot](./example/plugins/demo.py)
