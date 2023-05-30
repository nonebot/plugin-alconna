# Nonebot Plugin Alconna 文档

本文分为三部分:
- [`nonebot_plugin_alconna` 的介绍与使用](#plugin)
- [`Alconna` 本体的介绍与使用](#alconna)
- [外部参考](#references)

## Plugin

### 安装

```shell
pip install nonebot-plugin-alconna
```

或

```shell
nb plugin install nonebot-plugin-alconna
```

### 基础使用

本插件提供了一类新的事件响应器辅助函数 `on_alconna`, 其使用 `Alconna` 作为命令解析器。

```python
def on_alconna(
    command: Alconna | str,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = False,
    output_converter: Callable[[OutputType, str], Message | Awaitable[Message]] | None = None,
    aliases: set[str | tuple[str, ...]] | None = None,
    comp_config: CompConfig | None = None,
    ...,
):
```

- `command`: Alconna 命令
- `skip_for_unmatch`: 是否在命令不匹配时跳过该响应
- `auto_send_output`: 是否自动发送输出信息并跳过响应
- `output_converter`: 输出信息字符串转换为 Message 方法
- `aliases`: 命令别名, 作用类似于 `on_command` 中的 aliases
- `comp_config`: 补全会话配置, 不传入则不启用补全会话

### 依赖注入

`Alconna` 的解析结果会放入 `Arparma` 类中，或用户指定的 `Duplication` 类。


本插件提供了一系列依赖注入函数，便于在响应函数中获取解析结果：

- `AlconnaResult`: `CommandResult` 类型的依赖注入函数
- `AlconnaMatches`: `Arparma` 类型的依赖注入函数
- `AlconnaDuplication`: `Duplication` 类型的依赖注入函数
- `AlconnaMatch`: `Match` 类型的依赖注入函数
- `AlconnaQuery`: `Query` 类型的依赖注入函数

可以看到，本插件提供了几类额外的模型：
- `CommandResult`: 解析结果，包括了源命令 `command: Alconna` ，解析结果 `result: Arparma`，以及可能的输出信息 `output: str | None` 字段
- `Match`: 匹配项，表示参数是否存在于 `all_matched_args` 内，可用 `Match.available` 判断是否匹配，`Match.result` 获取匹配的值
- `Query`: 查询项，表示参数是否可由 `Arparma.query` 查询并获得结果，可用 `Query.available` 判断是否查询成功，`Query.result` 获取查询结果

同时，基于 [`Annotated` 支持](https://github.com/nonebot/nonebot2/pull/1832), 添加了两类注解:

- `AlcMatches`：同 `AlconnaMatches`
- `AlcResult`：同 `AlconnaResult`

实例:
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
    AlconnaMatches,
    AlcResult
)
from arclet.alconna import Alconna, Args, Option, Arparma

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
async def handle_test2(result: Arparma = AlconnaMatches()):
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

本插件可以通过 `handle(parameterless)` 来控制一个具体的响应函数是否在不满足条件时跳过响应。

```python
...
from nonebot import require
require("nonebot_plugin_alconna")
...

from arclet.alconna import Alconna, Subcommand, Option, Args
from nonebot_plugin_alconna import assign, on_alconna, AlconnaResult, CommandResult, Check

pip = Alconna(
    "pip",
    Subcommand("install", Args["pak", str], Option("--upgrade"), Option("--force-reinstall")),
    Subcommand("list", Option("--out-dated"))
)

pip_cmd = on_alconna(pip)

# 仅在命令为 `pip install` 并且 pak 为 `pip` 时响应
@pip_cmd.handle([Check(assign("install.pak", "pip"))])
async def update(arp: CommandResult = AlconnaResult()):
    ...

# 仅在命令为 `pip list` 时响应
@pip_cmd.handle([Check(assign("list"))])
async def list_(arp: CommandResult = AlconnaResult()):
    ...

# 仅在命令为 `pip install` 时响应
@pip_cmd.handle([Check(assign("install"))])
async def install(arp: CommandResult = AlconnaResult()):
    ...
```

## MessageSegment 标注

本插件提供了一系列便捷的 `MessageSegment` 标注，可用于匹配消息中除 text 外的其他 `MessageSegment`，也可用于快速创建 `MessageSegment`。

所有标注位于 `nonebot_plugin_alconna.adapters` 中。

### 通用标注

- `Text`: str 的别名
- `At`: 匹配 `At`/`Mention` 类型的 `MessageSegment`，例如 `Onebot 11` 中的 `At` 和 `Onebot 12` 中的 `Mention`
- `Image`: 匹配 `Image` 类型的 `MessageSegment`
- `Audio`: 匹配 `Audio` 类型的 `MessageSegment`
- `Voice`: 匹配 `Voice` 类型的 `MessageSegment`
- `File`: 匹配 `File` 类型的 `MessageSegment`
- `Video`: 匹配 `Video` 类型的 `MessageSegment`

此类标注无法用于创建 `MessageSegment`。

### 适配器标注

本插件为以下设配器提供了seg标注，可用于匹配各适配器的 `MessageSegment`，也可用于创建 `MessageSegment`：


| 协议名称                                                                | 路径                                   |
|---------------------------------------------------------------------|--------------------------------------|
| [OneBot 协议](https://github.com/nonebot/adapter-onebot)              | adapters.onebot11, adapters.onebot12 |
| [Telegram](https://github.com/nonebot/adapter-telegram)             | adapters.telegram                    |
| [飞书](https://github.com/nonebot/adapter-feishu)                     | adapters.feishu                      |
| [GitHub](https://github.com/nonebot/adapter-github)                 | adapters.github                      |
| [QQ 频道](https://github.com/nonebot/adapter-qqguild)                 | adapters.qqguild                     |
| [钉钉](https://github.com/nonebot/adapter-ding)                       | adapters.ding                        |
| [Console](https://github.com/nonebot/adapter-console)               | adapters.console                     |
| [开黑啦](https://github.com/Tian-que/nonebot-adapter-kaiheila)         | adapters.kook                        |
| [Mirai](https://github.com/ieew/nonebot_adapter_mirai2)             | adapters.mirai                       |
| [Ntchat](https://github.com/JustUndertaker/adapter-ntchat)          | adapters.ntchat                      |
| [MineCraft](https://github.com/17TheWord/nonebot-adapter-minecraft) | adapters.minecraft                   |
| [BiliBili Live](https://github.com/wwweww/adapter-bilibili)         | adapters.bilibili                    |
| [Walle-Q](https://github.com/onebot-walle/nonebot_adapter_walleq)   | adapters.onebot12                    |

### 示例

特定适配器:

```python
from nonebot_plugin_alconna.adapters.onebot12 import Mention
from nonebot.adapters.onebot.v12 import Message
from arclet.alconna import Alconna, Args

msg = Message(["Hello!", Mention("123")])
print(msg)  # Hello![mention:user_id=123]

alc = Alconna("Hello!", Args["target", Mention])
assert alc.parse(msg).query("target").data['user_id'] == '123'
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
assert alc.parse(msg1).query("target").data['user_id'] == '123'
assert alc.parse(msg2).query("target").data['qq'] == 123
```

## Alconna

[`Alconna`](https://github.com/ArcletProject/Alconna) 隶属于 `ArcletProject`, 是一个简单、灵活、高效的命令参数解析器, 并且不局限于解析命令式字符串。

其特点有:

* 高效
* 直观的命令组件创建方式
* 强大的类型解析与类型转换功能
* 自定义的帮助信息格式与命令解析控制
* 多语言支持
* 易用的快捷命令创建与使用
* 可创建命令补全会话, 以实现多轮连续的补全提示
* 模糊匹配、输出捕获等一众特性

## References

官方文档: [👉指路](https://arclet.top/)

QQ 交流群: [链接](https://jq.qq.com/?_wv=1027&k=PUPOnCSH)

友链: [📚文档](https://graiax.cn/guide/message_parser/alconna.html)