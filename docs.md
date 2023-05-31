# Nonebot Plugin Alconna 文档

本文分为三部分:
- [`nonebot_plugin_alconna` 的介绍与使用](#plugin)
- [`Alconna` 本体的介绍与使用](#alconna)
- [外部参考](#references)

## Plugin

### 展示

```python
from nonebot.adapters.onebot.v12 import Message, MessageSegment as Ob12MS
from nonebot_plugin_alconna import on_alconna, AlconnaMatches
from nonebot_plugin_alconna.adapters import At
from nonebot_plugin_alconna.adapters.onebot12 import Image
from arclet.alconna import Alconna, Args, Option, Arparma

alc = Alconna("Hello!", Option("--spec", Args["target", At]))
hello = on_alconna(alc, auto_send_output=True)

@hello.handle()
async def _(result: Arparma = AlconnaMatches()):
    if result.find("spec"):
        target: Ob12MS = result.query("spec.target")
        seed = target.data['user_id']
        await hello.finish(Message(Image(await gen_image(seed))))
    else:
        await hello.finish("Hello!")
```

### 安装

```shell
pip install nonebot-plugin-alconna
```

或

```shell
nb plugin install nonebot-plugin-alconna
```

### 基础使用

本插件提供了一类新的事件响应器辅助函数 `on_alconna`， 其使用 `Alconna` 作为命令解析器。

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
- `aliases`: 命令别名， 作用类似于 `on_command` 中的 aliases
- `comp_config`: 补全会话配置， 不传入则不启用补全会话

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

### 条件控制

本插件可以通过 `handle(parameterless)` 来控制一个具体的响应函数是否在不满足条件时跳过响应。

例如:
- `pip.handle([Check(assign("install.pak", "pip"))])` 表示仅在命令为 `pip install` 并且 pak 为 `pip` 时响应
- `pip.handle([Check(assign("list"))])` 表示仅在命令为 `pip list` 时响应
- `pip.handle([Check(assign("install"))])` 表示仅在命令为 `pip install` 时响应

### MessageSegment 标注

本插件提供了一系列便捷的 `MessageSegment` 标注。

标注可用于在 `Alconna` 中匹配消息中除 text 外的其他 `MessageSegment`，也可用于快速创建各适配器下的 `MessageSegment`。

所有标注位于 `nonebot_plugin_alconna.adapters` 中。

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
    Option("-v|--version", action=count),
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

他们拥有如下共同参数：

- `help_text`: 传入该组件的帮助信息
- `dest`: 被指定为解析完成时标注匹配结果的标识符，不传入时默认为选项或子命令的名称 (name)
- `requires`: 一段指定顺序的字符串列表，作为唯一的前置序列与命令嵌套替换
- `default`: 默认值，在该组件未被解析时使用使用该值替换。


### 选项操作

`Option` 可以特别设置传入一类 `Action`，作为解析操作

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

### 半自动补全

半自动补全为用户提供了推荐后续输入的功能。

补全默认通过 `--comp` 或 `-cp` 触发：（命名空间配置可修改名称）

### 快捷指令

快捷指令顾名思义，可以为基础指令创建便捷的触发方式

一般情况下你可以通过 `Alconna.shortcut` 进行快捷指令操作 (创建，删除)；

```python
>>> from arclet.alconna import Alconna, Args
>>> alc = Alconna("setu", Args["count", int])
>>> alc.shortcut("涩图(\d+)张", {"args": ["{0}"]})
'Alconna::setu 的快截指令: "涩图(\\d+)张" 添加成功'
>>> alc.parse("涩图3张").query("count")
3
```

### 使用模糊匹配

模糊匹配通过在 Alconna 中设置其 CommandMeta 开启。

模糊匹配会应用在任意需要进行名称判断的地方，如**命令名称**，**选项名称**和**参数名称**（如指定需要传入参数名称）。

### Args

**Args** 用于指定 Alconna 的中的参数，其样式类似于 python中函数的参数与类型注解。

```python
Args["foo", str]["bar", int, 1]
```


### Arparma

`Alconna.parse` 会返回由 **Arparma** 承载的解析结果。

`Arparma` 同时提供了便捷的查询方法 `query()`，会根据传入的 `path` 查找参数并返回

同样, `Arparma["foo.bar"]` 的表现与 `query()` 一致


### Duplication

**Duplication** 用来提供更好的自动补全。

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
class MyDup(Duplication):
    package: str
    file: Optional[str] = None
    url: Optional[str] = None
```

## References

插件仓库: [📦](https://github.com/ArcletProject/nonebot-plugin-alconna)

官方文档: [👉指路](https://arclet.top/)

QQ 交流群: [链接](https://jq.qq.com/?_wv=1027&k=PUPOnCSH)

友链: [📚文档](https://graiax.cn/guide/message_parser/alconna.html)