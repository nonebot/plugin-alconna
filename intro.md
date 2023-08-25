# Nonebot Plugin Alconna 介绍

## 安装

```shell
pip install nonebot-plugin-alconna
```

或

```shell
nb plugin install nonebot-plugin-alconna
```

## 概览

该插件使用 [`Alconna`](https://github.com/ArcletProject/Alconna) 作为命令解析器，
其是一个简单、灵活、高效的命令参数解析器, 并且不局限于解析命令式字符串。

其特点包括:

* 高效
* 直观的命令组件创建方式
* 强大的类型解析与类型转换功能
* 自定义的帮助信息格式
* 多语言支持
* 易用的快捷命令创建与使用
* 可创建命令补全会话, 以实现多轮连续的补全提示
* 可嵌套的多级子命令
* 正则匹配支持

该插件提供了一类新的事件响应器辅助函数 `on_alconna`，以及 `AlconnaResult` 等依赖注入函数。

同时，基于 [`Annotated` 支持](https://github.com/nonebot/nonebot2/pull/1832), 添加了两类注解 `AlcMatches` 与`AlcResult`

该插件还可以通过 `handle(parameterless)` 来控制一个具体的响应函数是否在不满足条件时跳过响应。

例如:
- `pip.handle([Check(assign("add.name", "nb"))])` 表示仅在命令为 `role-group add` 并且 name 为 `nb` 时响应
- `pip.handle([Check(assign("list"))])` 表示仅在命令为 `role-group list` 时响应
- `pip.handle([Check(assign("add"))])` 表示仅在命令为 `role-group add` 时响应

该插件基于 `Alconna` 的特性，同时提供了一系列便捷的 `MessageSegment` 标注。

标注可用于在 `Alconna` 中匹配消息中除 text 外的其他 `MessageSegment`，也可用于快速创建各适配器下的 `MessageSegment`。

所有标注位于 `nonebot_plugin_alconna.adapters` 中。

## 展示

```python
from nonebot.adapters.onebot.v12 import Message
from nonebot_plugin_alconna import on_alconna, AlconnaMatches, At
from nonebot_plugin_alconna.adapters.onebot12 import Image
from arclet.alconna import Alconna, Args, Option, Arparma, Subcommand, MultiVar

alc = Alconna(
    "role-group",
    Subcommand(
        "add", Args["name", str],
        Option("member", Args["target", MultiVar(At)]),
    ),
    Option("list"),
)
rg = on_alconna(alc, auto_send_output=True)

@rg.handle()
async def _(result: Arparma = AlconnaMatches()):
    if result.find("list"):
        img = await gen_role_group_list_image()
        await rg.finish(Message([Image(img)]))
    if result.find("add"):
        group = await create_role_group(result["add.name"])
        if result.find("add.member"):
            ats: tuple[At] = result["add.member.target"]
            group.extend(member.target for member in ats)
        await rg.finish("添加成功")
```

我们可以看到主要的两大组件：**Option** 与 **Subcommand**。

`Option` 可以传入一组 `alias`，如 `Option("--foo|-F|--FOO|-f")` 或 `Option("--foo", alias=["-F"]`

`Subcommand` 则可以传入自己的 **Option** 与 **Subcommand**：

他们拥有如下共同参数：

- `help_text`: 传入该组件的帮助信息
- `dest`: 被指定为解析完成时标注匹配结果的标识符，不传入时默认为选项或子命令的名称 (name)
- `requires`: 一段指定顺序的字符串列表，作为唯一的前置序列与命令嵌套替换
- `default`: 默认值，在该组件未被解析时使用使用该值替换。

其次使用了 `MessageSegment` 标注，其中 `At` 属于通用标注，而 `Image` 属于 `onebot12` 适配器下的标注。

`on_alconna` 的所有参数如下：

- `command: Alconna | str`: Alconna 命令
- `skip_for_unmatch: bool = True`: 是否在命令不匹配时跳过该响应
- `auto_send_output: bool = False`: 是否自动发送输出信息并跳过响应
- `output_converter: TConvert | None = None`: 输出信息字符串转换为 Message 方法
- `aliases: set[str | tuple[str, ...]] | None = None`: 命令别名， 作用类似于 `on_command` 中的 aliases
- `comp_config: CompConfig | None = None`: 补全会话配置， 不传入则不启用补全会话
- `use_origin: bool = False`: 是否使用未经 to_me 等处理过的消息
- `use_cmd_start`: 是否使用 COMMAND_START 作为命令前缀

`AlconnaMatches` 是一个依赖注入函数，可注入 `Alconna` 命令解析结果。

## References

插件文档: [📦这里](https://github.com/ArcletProject/nonebot-plugin-alconna/blob/master/docs.md)

官方文档: [👉指路](https://arclet.top/)

QQ 交流群: [🔗链接](https://jq.qq.com/?_wv=1027&k=PUPOnCSH)

友链: [📚文档](https://graiax.cn/guide/message_parser/alconna.html)