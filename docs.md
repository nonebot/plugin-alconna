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

### 展示

```python
from nonebot.adapters.onebot.v12 import Message
from nonebot_plugin_alconna import on_alconna, AlconnaMatches, At
from nonebot_plugin_alconna.adapters.onebot12 import Image
from arclet.alconna import Alconna, Args, Option, Arparma

alc = Alconna("Hello!", Option("--spec", Args["target", At]))
hello = on_alconna(alc, auto_send_output=True)

@hello.handle()
async def _(result: Arparma = AlconnaMatches()):
    if result.find("spec"):
        target = result.query[At]("spec.target")
        seed = target.target
        await hello.finish(Message(Image(await gen_image(seed))))
    else:
        await hello.finish("Hello!")
```

### 基础使用

本插件提供了一类新的事件响应器辅助函数 `on_alconna`， 其使用 `Alconna` 作为命令解析器。

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
    ...,
):
```

- `command`: Alconna 命令或字符串，字符串将通过 `AlconnaFormat` 转换为 Alconna 命令
- `skip_for_unmatch`: 是否在命令不匹配时跳过该响应
- `auto_send_output`: 是否自动发送输出信息并跳过响应
- `aliases`: 命令别名， 作用类似于 `on_command` 中的 aliases
- `comp_config`: 补全会话配置， 不传入则不启用补全会话
- `extensions`: 需要加载的匹配扩展, 可以是扩展类或扩展实例
- `exclude_ext`: 需要排除的匹配扩展, 可以是扩展类或扩展的id
- `use_origin`: 是否使用未经 to_me 等处理过的消息
- `use_cmd_start`: 是否使用 COMMAND_START 作为命令前缀
- `use_cmd_sep`: 是否使用 COMMAND_SEP 作为命令分隔符

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

若设置配置项 **ALCONNA_USE_PARAM** (默认为 True) 为 True，则上述依赖注入的目标参数皆不需要使用依赖注入函数：

```python
async def handle(
    result: CommandResult,
    arp: Arparma,
    dup: Duplication,
    source: Alconna,
    abc: str,  # 类似 Match, 但是若匹配结果不存在对应字段则跳过该 handler
    foo: Match[str],
    bar: Query[int] = Query("ttt.bar", 0)  # Query 仍然需要一个默认值来传递 path 参数
):
    ...
```

该效果对于 `got_path` 下的 Arg 同样有效

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
async def handle_test2(result: Arparma):
    await test.send(f"head result: {result.header_result}")
    await test.send(f"args: {result.all_matched_args}")

@test.handle()
async def handle_test3(bar: Match[int] = AlconnaMatch("bar")):
    if bar.available:    
        await test.send(f"foo={bar.result}")

@test.handle()
async def handle_test4(qux: Query[bool] = Query("baz.qux", False)):
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

或者使用 `AlconnaMatcher.assign`：

```python
@pip_cmd.assign("install.pak", "pip")
async def update(arp: CommandResult = AlconnaResult()):
    ...

# 仅在命令为 `pip list` 时响应
@pip_cmd.assign("list")
async def list_(arp: CommandResult = AlconnaResult()):
    ...

# 仅在命令为 `pip install` 时响应
@pip_cmd.assign("install")
async def install(arp: CommandResult = AlconnaResult()):
    ...
```

此外，还能像 `CommandGroup` 一样为每个分发设置独立的 matcher：

```python
update_cmd = pip_cmd.dispatch("install.pak", "pip")

@update_cmd.handle()
async def update(arp: CommandResult = AlconnaResult()):
    ...
```

### 便捷装饰器

本插件提供了一个 `funcommand` 装饰器, 其用于将一个接受任意参数，
返回 `str` 或 `Message` 或 `MessageSegment` 的函数转换为命令响应器。

```python
from nonebot_plugin_alconna import funcommand

@funcommand()
async def echo(msg: str):
    return msg
```

### 匹配拓展

本插件提供了一个 `Extension` 类，其用于拓展 AlconnaMatcher 的行为。

例如：

```python
from nonebot_plugin_alconna import Extension, Alconna, on_alconna

class LLMExtension(Extension):
    @property
    def priority(self) -> int:
        return 10

    @property
    def id(self) -> str:
        return "LLMExt"
    
    def __init__(self, llm):
      self.llm = llm
    
    def post_init(self, alc: Alconna) -> None:
        self.llm.add_context(alc.command, alc.meta.description)

    async def message_provider(
        self, event, state, bot, use_origin: bool = False
    ):
        if event.get_type() != "message":
            return 
        resp = await self.llm.input(str(event.get_message()))
        return event.get_message().__class__(resp.content)

matcher = on_alconna(Alconna(...), extensions=[DemoExtension(LLM)])
...
```

## MessageSegment 标注

本插件提供了一系列便捷的 `MessageSegment` 标注，可用于匹配消息中除 text 外的其他 `MessageSegment`，也可用于快速创建 `MessageSegment`。

### 通用标注

通用标注会将符合条件的 `MessageSegment` 转为插件提供的内部类型

```python
class Segment:
    ...

class Text(Segment):
    text: str
    style: Optional[str]

class At(Segment):
    type: Literal["user", "role", "channel"]
    target: str

class AtAll(Segment):
    ...
    
class Emoji(Segment):
    id: str
    name: Optional[str]
    
class Media(Segment):  # Image, Audio, Voice, Video
    url: Optional[str]
    id: Optional[str]
    path: Optional[str]
    raw: Optional[bytes]
    name: Optional[str]

class File(Segment):
    id: str
    name: Optional[str]
    raw: Optional[bytes]

class Reply(Segment):
    origin: Any
    id: str
    msg: Optional[Union[Message, str]]

class Card(Segment):
    raw: str
    content: Optional[dict]

class Other(Segment):
    origin: MessageSegment
```

- `Text`: 匹配 `Text` 类型的 `MessageSegment`.
- `At`: 匹配 `At`/`Mention` 类型的 `MessageSegment`，例如 `Onebot 11` 中的 `At` 和 `Onebot 12` 中的 `Mention`
- `AtAll`: 匹配 `AtAll`/`MentionAll` 类型的 `MessageSegment`，例如 `mirai2` 中的 `AtAll` 和 `Onebot 12` 中的 `MentionAll`
- `Image`: 匹配 `Image` 类型的 `MessageSegment`
- `Audio`: 匹配 `Audio` 类型的 `MessageSegment`
- `Voice`: 匹配 `Voice` 类型的 `MessageSegment`
- `File`: 匹配 `File` 类型的 `MessageSegment`
- `Video`: 匹配 `Video` 类型的 `MessageSegment`
- `Emoji`: 匹配 `Emoji` 类型的 `MessageSegment`
- `Card`: 匹配 `Card` 类型的 `MessageSegment`，对应如 `qq` 中的小程序卡片
- `Other`: 匹配除以上类型外的 `MessageSegment`

此类标注通过 `UniMessage.export` 可以转为特定的 `MessageSegment`。

### 通用消息

除了以上通用标注外，本插件还提供了一个类似于 `Message` 的 `UniMessage` 类型，其元素为经过通用标注转换后的 `Segment`。

你可以通过提供的 `UniversalMessage` 或 `UniMsg` 依赖注入器来获取 `UniMessage`。

`UniMessage` 可以通过 `UniMessage.export` 转为 `Message`，以达到跨平台发送消息的目的。

```python
from nonebot_plugin_alconna import UniMsg, At, Reply

matcher = on_xxx(...)

@matcher.handle()
async def _(msg: UniMsg):
    reply = msg[Reply, 0]
    print(reply.origin)
    if msg.has(At):
        ats = msg.get(At)
        await matcher.send(await ats.export())
    ...
```

`AlconnaMatcher` 的 `send` 方法也支持 `UniMessage` 类型，你可以直接将 `UniMessage` 传入 `send` 方法，无需手动转换.

### 适配器标注

本插件为以下设配器提供了seg标注，可用于匹配各适配器的 `MessageSegment`，也可用于创建 `MessageSegment`：


| 协议名称                                                                | 路径                                   |
|---------------------------------------------------------------------|--------------------------------------|
| [OneBot 协议](https://github.com/nonebot/adapter-onebot)              | adapters.onebot11, adapters.onebot12 |
| [Telegram](https://github.com/nonebot/adapter-telegram)             | adapters.telegram                    |
| [飞书](https://github.com/nonebot/adapter-feishu)                     | adapters.feishu                      |
| [GitHub](https://github.com/nonebot/adapter-github)                 | adapters.github                      |
| [QQ bot](https://github.com/nonebot/adapter-qq)                     | adapters.qq                          |
| [QQ 频道](https://github.com/nonebot/adapter-qqguild)                 | adapters.qqguild                     |
| [钉钉](https://github.com/nonebot/adapter-ding)                       | adapters.ding                        |
| [Console](https://github.com/nonebot/adapter-console)               | adapters.console                     |
| [开黑啦](https://github.com/Tian-que/nonebot-adapter-kaiheila)         | adapters.kook                        |
| [Mirai](https://github.com/ieew/nonebot_adapter_mirai2)             | adapters.mirai                       |
| [Ntchat](https://github.com/JustUndertaker/adapter-ntchat)          | adapters.ntchat                      |
| [MineCraft](https://github.com/17TheWord/nonebot-adapter-minecraft) | adapters.minecraft                   |
| [BiliBili Live](https://github.com/wwweww/adapter-bilibili)         | adapters.bilibili                    |
| [Walle-Q](https://github.com/onebot-walle/nonebot_adapter_walleq)   | adapters.onebot12                    |
| [Villa](https://github.com/CMHopeSunshine/nonebot-adapter-villa)    | adapters.villa                       |
| [Discord](https://github.com/nonebot/adapter-discord)               | adapters.discord                     |
| [Red 协议](https://github.com/nonebot/adapter-red)                    | adapters.red                         |


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
from nonebot_plugin_alconna import At
from arclet.alconna import Alconna, Args

msg1 = Ob12M(["Hello!", Ob12MS.mention("123")]) # Hello![mention:user_id=123]
msg2 = Ob11M(["Hello!", Ob11MS.at(123)]) # Hello![CQ:at,qq=123]


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

## Alconna

[`Alconna`](https://github.com/ArcletProject/Alconna) 隶属于 `ArcletProject`，是一个简单、灵活、高效的命令参数解析器, 并且不局限于解析命令式字符串。


示例的 `Alconna` 使用:

```python
from arclet.alconna import Alconna, Args, Option, Subcommand, count

alc = Alconna(
    "pip",
    Subcommand(
        "install",
        Args["package", str],
        Option("-r|--requirement", Args["file", str]),
        Option("-i|--index-url", Args["url", str]),
    ),
    Option("-v|--version"),
    Option("-v|--verbose", action=count),
)

print(alc.parse("pip install nonebot2 -i https://mirrors.aliyun.com/pypi/simple/").all_matched_args)
# {'package': 'nonebot2', 'url': 'https://mirrors.aliyun.com/pypi/simple/'}
```

其特点有:

* 高效
* 直观的命令组件创建方式，例如选项别名，默认值，解析操作等
* 强大的类型解析与类型转换功能，具体在 `Args` 的使用上
* 自定义的帮助信息格式，帮助信息由内置选项 `help` 触发，用户可以选择自定义的 TextFormatter 获得不一样的输出格式
* 多语言支持，目前支持中文与英文
* 易用的快捷命令创建与使用，可由内置选项 `shortcut` 触发，或使用 `Alconna.shortcut()` 方法
* 可创建命令补全会话, 以实现多轮连续的补全提示
* 可通过 `Namespace`，`CommandMeta` 配置命令的行为与属性，例如通过 `Namespace` 自定义内置选项的触发字段，或通过 `CommandMeta` 启用模糊匹配
* 可嵌套的多级子命令
* `Duplication` 能像 `argparse.Namespace` 一样获取指定的解析结果并获得类型支持
* 正则匹配支持
* ...

### 组件

`Alconna` 拥有两大组件：**Option** 与 **Subcommand**。

`Option` 可以传入一组 `alias`，如 `Option("--foo|-F|--FOO|-f")` 或 `Option("--foo", alias=["-F"]`

`Subcommand` 则可以传入自己的 **Option** 与 **Subcommand**：

```python
from arclet.alconna import Alconna, Option, Subcommand

alc = Alconna(
    "command_name",
    Option("opt1"),
    Option("--opt2"),
    Subcommand(
        "sub1",
        Option("sub1_opt1"),
        Option("-SO2"),
        Subcommand(
            "sub1_sub1"
        )
    ),
    Subcommand(
        "sub2"
    )
)
```

他们拥有如下共同参数：

- `help_text`: 传入该组件的帮助信息

- `dest`: 被指定为解析完成时标注匹配结果的标识符，不传入时默认为选项或子命令的名称 (name)

- `requires`: 一段指定顺序的字符串列表，作为唯一的前置序列与命令嵌套替换

  对于命令 `test foo bar baz qux <a:int>` 来讲，因为`foo bar baz` 仅需要判断是否相等, 所以可以这么编写：

  ```python
  Alconna("test", Option("qux", Args.a[int], requires=["foo", "bar", "baz"]))
  ```

- `default`: 默认值，在该组件未被解析时使用使用该值替换。

  特别的，使用 `OptionResult` 或 `SubcomanndResult` 可以设置包括参数字典在内的默认值：

  ```python
  from arclet.alconna import Option, OptionResult

  opt1 = Option("--foo", default=False)
  opt2 = Option("--foo", default=OptionResult(value=False, args={"bar": 1}))
  ```

### 选项操作

`Option` 可以特别设置传入一类 `Action`，作为解析操作

`Action` 分为三类：
- `store`: 无 Args 时， 仅存储一个值， 默认为 Ellipsis； 有 Args 时， 后续的解析结果会覆盖之前的值
- `append`: 无 Args 时， 将多个值存为列表， 默认为 Ellipsis； 有 Args 时， 每个解析结果会追加到列表中

  当存在默认值并且不为列表时， 会自动将默认值变成列表， 以保证追加的正确性
- `count`: 无 Args 时， 计数器加一； 有 Args 时， 表现与 STORE 相同

  当存在默认值并且不为数字时， 会自动将默认值变成 1， 以保证计数器的正确性。

`Alconna` 提供了预制的几类 `action`：
- `store`，`store_value`，`store_true`，`store_false`
- `append`，`append_value`
- `count`

### 紧凑命令

`Alconna`, `Option` 与 `Subcommand` 可以设置 `compact=True` 使得解析命令时允许名称与后随参数之间没有分隔：

```python
from arclet.alconna import Alconna, Option, CommandMeta, Args

alc = Alconna("test", Args["foo", int], Option("BAR", Args["baz", str], compact=True), meta=CommandMeta(compact=True))

assert alc.parse("test123 BARabc").matched
```

这使得我们可以实现如下命令：

```python
>>> from arclet.alconna import Alconna, Option, Args, append
>>> alc = Alconna("gcc", Option("--flag|-F", Args["content", str], action=append, compact=True))
>>> alc.parse("gcc -Fabc -Fdef -Fxyz").query[list]("flag.content")
['abc', 'def', 'xyz']
```

当 `Option` 的 `action` 为 `count` 时，其自动支持 `compact` 特性：

```python
>>> from arclet.alconna import Alconna, Option, count
>>> alc = Alconna("pp", Option("--verbose|-v", action=count, default=0))
>>> alc.parse("pp -vvv").query[int]("verbose.value")
3
```

### 配置

`arclet.alconna.Namespace` 表示某一命名空间下的默认配置：

```python
from arclet.alconna import config, namespace, Namespace
from arclet.alconna.tools import ShellTextFormatter


np = Namespace("foo", prefixes=["/"])  # 创建 Namespace 对象，并进行初始配置

with namespace("bar") as np1:
    np1.prefixes = ["!"]    # 以上下文管理器方式配置命名空间，此时配置会自动注入上下文内创建的命令
    np1.formatter_type = ShellTextFormatter  # 设置此命名空间下的命令的 formatter 默认为 ShellTextFormatter
    np1.builtin_option_name["help"] = {"帮助", "-h"}  # 设置此命名空间下的命令的帮助选项名称

config.namespaces["foo"] = np  # 将命名空间挂载到 config 上
```

同时也提供了默认命名空间配置与修改方法：

```python
from arclet.alconna import config, namespace, Namespace


config.default_namespace.prefixes = [...]  # 直接修改默认配置

np = Namespace("xxx", prefixes=[...])
config.default_namespace = np  # 更换默认的命名空间

with namespace(config.default_namespace.name) as np:
    np.prefixes = [...]
```

### 半自动补全

半自动补全为用户提供了推荐后续输入的功能。

补全默认通过 `--comp` 或 `-cp` 触发：（命名空间配置可修改名称）

```python
from arclet.alconna import Alconna, Args, Option

alc = Alconna("test", Args["abc", int]) + Option("foo") + Option("bar")
alc.parse("test --comp")

'''
output

以下是建议的输入：
* <abc: int>
* --help
* -h
* -sct
* --shortcut
* foo
* bar
'''
```

### 快捷指令

快捷指令顾名思义，可以为基础指令创建便捷的触发方式

一般情况下你可以通过 `Alconna.shortcut` 进行快捷指令操作 (创建，删除)；

```python
>>> from arclet.alconna import Alconna, Args
>>> alc = Alconna("setu", Args["count", int])
>>> alc.shortcut("涩图(\d+)张", {"args": ["{0}"]})
'Alconna::setu 的快捷指令: "涩图(\\d+)张" 添加成功'
>>> alc.parse("涩图3张").query("count")
3
```

`shortcut` 的第一个参数为快捷指令名称，第二个参数为 `ShortcutArgs`，作为快捷指令的配置

```python
class ShortcutArgs(TypedDict):
    """快捷指令参数"""

    command: NotRequired[DataCollection[Any]]
    """快捷指令的命令"""
    args: NotRequired[list[Any]]
    """快捷指令的附带参数"""
    fuzzy: NotRequired[bool]
    """是否允许命令后随参数"""
    prefix: NotRequired[bool]
    """是否调用时保留指令前缀"""
```

当 `fuzzy` 为 False 时，传入 `"涩图1张 abc"` 之类的快捷指令将视为解析失败

快捷指令允许三类特殊的 placeholder:

- `{%X}`: 如 `setu {%0}`，表示此处填入快捷指令后随的第 X 个参数。

  例如，若快捷指令为 `涩图`, 配置为 `{"command": "setu {%0}"}`, 则指令 `涩图 1` 相当于 `setu 1`
- `{*}`: 表示此处填入所有后随参数，并且可以通过 `{*X}` 的方式指定组合参数之间的分隔符。
- `{X}`: 表示此处填入可能的正则匹配的组：
  - 若 `command` 中存在匹配组 `(xxx)`，则 `{X}` 表示第 X 个匹配组的内容
  - 若 `command` 中存储匹配组 `(?P<xxx>...)`, 则 `{X}` 表示名字为 X 的匹配结果

除此之外, 通过内置选项 `--shortcut` 可以动态操作快捷指令。

例如： 
- `cmd --shortcut <key> <cmd>` 来增加一个快捷指令
- `cmd --shortcut list` 来列出当前指令的所有快捷指令
- `cmd --shortcut delete key` 来删除一个快捷指令

### 使用模糊匹配

模糊匹配通过在 Alconna 中设置其 CommandMeta 开启。

模糊匹配会应用在任意需要进行名称判断的地方，如**命令名称**，**选项名称**和**参数名称**（如指定需要传入参数名称）。

```python
from arclet.alconna import Alconna, CommandMeta

alc = Alconna("test_fuzzy", meta=CommandMeta(fuzzy_match=True))
alc.parse("test_fuzy")
# output: test_fuzy is not matched. Do you mean "test_fuzzy"?
```

### Args

**Args** 在 Alconna 中有非常重要的地位，甚至称得上是核心，比 Alconna 重要十倍甚至九倍。

其通常以 `Args[key1, var1, default1][key2, var2][Arg(key3, var3), Arg(key4, var4, default4)][...]` 的方式构造一个 Args。

其中，key 一定是字符串，而 var 一般为参数的类型，default 为具体的值或者 **arclet.alconna.args.Field**。

#### key

`key` 的作用是用以标记解析出来的参数并存放于 **Arparma** 中，以方便用户调用。

其有三种为 Args 注解的标识符，为 `?`、`/` 与 `!`。标识符与 key 之间建议以 `;` 分隔：

- `!` 标识符表示该处传入的参数应不是规定的类型，或不在指定的值中。
- `?` 标识符表示该参数为可选参数，会在无参数匹配时跳过。
- `/` 标识符表示该参数的类型注解需要隐藏。

另外，对于参数的注释也可以标记在 `key` 中，其与 key 或者标识符 以 `#` 分割：

`foo#这是注释;?` 或 `foo?#这是注释`

#### var

var 负责命令参数的类型检查与类型转化

var 可以是以下几类：

- 存在于 `nepattern.pattern_map` 中的类型/字符串，用以替换为预制好的 **BasePattern**
- 字符串
  - 若字符串以 `"re:"` 打头，表示将其转为正则解析表达式，并且返回类型为匹配字符串
  - 若字符串以 `"rep:"` 打头，表示将其转为特殊的 `RegexPattern`，并且返回类型为 `re.Match`
  - 其他字符串将作为直接的比较对象
- 列表，其中可存放 **BasePattern**、类型或者任意参数值，如字符串或者数字
- `Union`、`Optional`、`Literal` 等会尝试转换为 `List[Type]`
- `Dict[type1，type2]`、`List[type]`、`Set[type]`
- 一般的类型，其会尝试比较传入参数的类型是否与其相关
- **AnyOne**、**AllParam**，作为泛匹配的标识符
- **AnyString**, 会将传入的任意参数转为字符串
- 预制好的字典, 表示传入值依据该字典的键决定匹配结果
- `Annotated[type, Callable[..., bool], ...]`，表示为某一类型添加校验器
- `Callable[[P], T]`，表示会将传入的参数 P 经过该调用对象并将返回值 T 作为匹配结果
- ...

内置的类型检查包括 `int`、`str`、`float`、`bool`、`'url'`、`'ip'`、`'email'`、`list`、`dict`、`tuple`、`set`、`Any` 、`bytes`、`hex`、`datetime` 等。

若 `Arg` 只传入了 `key`，则 `var` 自动选择 `key` 的值作为比较对象

另外，`Alconna` 提供了两类特殊的类型用以实现限制功能：

- **MultiVar**：将该参数标记为需要获取可变数量或指定数量的数据，通过填入 `flag: int | Literal['+', '*']` 实现  
- **KeyWordVar**：将该参数标记为需要同时写入参数名才认定为合法参数，默认形式为 `key=arg`，可指定分隔符

当 **MultiVar** 与 **KeyWordVar** 一起使用时， 该参数表示为需要接收多个 `key=arg` 形式的数据， 类似 `**kwargs`

### Arparma

`Alconna.parse` 会返回由 **Arparma** 承载的解析结果。

`Arpamar` 会有如下参数：

- 调试类
  - matched: 是否匹配成功
  - error_data: 解析失败时剩余的数据
  - error_info: 解析失败时的异常内容
  - origin: 原始命令，可以类型标注

- 分析类
  - header_match: 命令头部的解析结果，包括原始头部、解析后头部、解析结果与可能的正则匹配组
  - main_args: 命令的主参数的解析结果
  - options: 命令所有选项的解析结果
  - subcommands: 命令所有子命令的解析结果
  - other_args: 除主参数外的其他解析结果
  - all_matched_args: 所有 Args 的解析结果

`Arparma` 同时提供了便捷的查询方法 `query[type]()`，会根据传入的 `path` 查找参数并返回

`path` 支持如下：
- `main_args`, `options`, ...: 返回对应的属性
- `args`: 返回 all_matched_args
- `main_args.xxx`, `options.xxx`, ...: 返回字典中 `xxx`键对应的值
- `args.xxx`: 返回 all_matched_args 中 `xxx`键对应的值
- `options.foo`, `foo`: 返回选项 `foo` 的解析结果 (OptionResult)
- `options.foo.value`, `foo.value`: 返回选项 `foo` 的解析值
- `options.foo.args`, `foo.args`: 返回选项 `foo` 的解析参数字典
- `options.foo.args.bar`, `foo.bar`: 返回选项 `foo` 的参数字典中 `bar` 键对应的值
...

同样, `Arparma["foo.bar"]` 的表现与 `query()` 一致


### Duplication

**Duplication** 用来提供更好的自动补全，类似于 **ArgParse** 的 **Namespace**，经测试表现良好（好耶）。

普通情况下使用，需要利用到 **ArgsStub**、**OptionStub** 和 **SubcommandStub** 三个部分，

以pip为例，其对应的 Duplication 应如下构造：

```python
from arclet.alconna import OptionResult, Duplication, SubcommandStub

class MyDup(Duplication):
    verbose: OptionResult
    install: SubcommandStub  # 选项与子命令对应的stub的变量名必须与其名字相同
```

并在解析时传入 Duplication：

```python
result = alc.parse("pip -v install ...", duplication=MyDup)
>>> type(result)
<class MyDup>
```

**Duplication** 也可以如 **Namespace** 一样直接标明参数名称和类型：

```python
from typing import Optional
from arclet.alconna import Duplication


class MyDup(Duplication):
    package: str
    file: Optional[str] = None
    url: Optional[str] = None
```

## References

Nonebot 文档: [📚文档](https://nonebot.dev/docs/next/best-practice/alconna/alconna)

官方文档: [👉指路](https://arclet.top/)

QQ 交流群: [🔗链接](https://jq.qq.com/?_wv=1027&k=PUPOnCSH)

友链: [📦这里](https://graiax.cn/guide/message_parser/alconna.html)