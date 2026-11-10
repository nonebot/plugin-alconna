# Nonebot Plugin Alconna 文档

本文分为三部分:
- [`nonebot_plugin_alconna` 的介绍与使用](#插件)
- [`Alconna` 本体的介绍与使用](#本体)(请优先阅读本体)
- [外部参考](#references)

## 插件
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

### 响应器使用

本插件基于 **Alconna** , 为 **Nonebot** 提供了一类新的事件响应器辅助函数 `on_alconna`.
```python
def on_alconna(
    command: Alconna | str,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = True,
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

其中对于 `skip_for_unmatch` 和 `auto_send_output` 的效果如下:

| skip \ auto | True           | False                         |
|-------------|----------------|-------------------------------|
| True        | 帮助文本等自动发送      | 帮助文本等不发送                      |
| False       | 帮助文本等和错误信息自动发送 | 帮助文本等和错误信息设置到 `CommandResult` |


`on_alconna` 返回的是 `Matcher` 的子类 `AlconnaMatcher`，其拓展了如下方法:

- `.assign(path, value, or_not)`: 用于对包含多个选项/子命令的命令的分派处理(具体请看条件控制)
- `.got_path(path, prompt, middleware)`: 在 `got` 方法的基础上，会以 path 对应的参数为准，读取传入 message 的最后一个消息段并验证转换
- `.set_path_arg(key, value)`, `.get_path_arg(key)`: 类似 `set_arg` 和 `got_arg`，为 `got_path` 的特化版本
- `.reject_path(path[, prompt, fallback])`: 类似于 `reject_arg`，对应 `got_path`
- `.dispatch`: 同样的分派处理，但是是类似 `CommandGroup` 一样返回新的 `AlconnaMatcher`
- `.got`, `send`, `reject`, ...: 拓展了 prompt 类型，即支持使用 `UniMessage` 作为 prompt

`assign`实例:

```python
from nonebot import require
require("nonebot_plugin_alconna")

from arclet.alconna import Alconna, Option, Args
from nonebot_plugin_alconna import on_alconna, AlconnaMatch, Match, UniMessage

  
login = on_alconna(Alconna(["/"], "login", Args["password?", str], Option("-r|--recall"))) # 这里["/"]指命令前缀必须是/

@login.assign("recall") # /login -r
async def login_exit():
    await login.finish("已退出")

@login.assign("password") # /login xxx
async def login_handle(pw: Match[str] = AlconnaMatch("password")):
    if pw.available:
        login.set_path_arg("password", pw.result)
```

`dispatch`每个分发设置独立的 matcher:

```python
update_cmd = pip_cmd.dispatch("install.pak", "pip")

@update_cmd.handle()
async def update(arp: CommandResult = AlconnaResult()):
    ...
```

`got_path`类似 Nonebot2 的got, 它与 `assign`，`Match`，`Query` 等地方一样，都需要指明 `path` 参数 (即对应 Arg 验证的路径)

`got_path` 会获取消息的最后一个消息段并转为 path 对应的类型，例如示例中 `target` 对应的 Arg 里要求 str 或 At，则 got 后用户输入的消息只有为 text 或 at 才能进入处理函数.

实例:

```python
from nonebot_plugin_alconna import At, Match, UniMessage, on_alconna


test_cmd = on_alconna(Alconna("test", Args["target?", Union[str, At]]))

@test_cmd.handle()
async def tt_h(target: Match[Union[str, At]]):
    if target.available:
        test_cmd.set_path_arg("target", target.result)

@test_cmd.got_path("target", prompt="请输入目标")
async def tt(target: Union[str, At]):
    await test_cmd.send(UniMessage(["ok\n", target]))
```

`path`支持 ~XXX 语法，其会把 ~ 替换为可能的父级路径:

```python
 pip = Alconna(
     "pip",
     Subcommand(
         "install",
         Args["pak", str],
         Option("--upgrade|-U"),
         Option("--force-reinstall"),
     ),
     Subcommand("list", Option("--out-dated")),
 )

 pipcmd = on_alconna(pip)
 pip_install_cmd = pipcmd.dispatch("install")


 @pip_install_cmd.assign("~upgrade")
 async def pip1_u(pak: Query[str] = Query("~pak")):
     await pip_install_cmd.finish(f"pip upgrading {pak.result}...")
```


### Alconna的依赖注入

本插件提供了一系列依赖注入函数，便于在响应函数中获取解析结果:

- `AlconnaResult`: `CommandResult` 类型的依赖注入函数
- `AlconnaMatches`: `Arparma` 类型的依赖注入函数
- `AlconnaDuplication`: `Duplication` 类型的依赖注入函数
- `AlconnaMatch`: `Match` 类型的依赖注入函数
- `AlconnaQuery`: `Query` 类型的依赖注入函数

同时，基于 [`Annotated` 支持](https://github.com/nonebot/nonebot2/pull/1832), 添加了两类注解:

- `AlcMatches`：同 `AlconnaMatches`
- `AlcResult`：同 `AlconnaResult`

可以看到，本插件提供了几类额外的模型:

- `CommandResult`: 解析结果，包括了源命令 `source: Alconna` ，解析结果 `result: Arparma`，以及可能的输出信息 `output: str | None` 字段
- `Match`: 匹配项，表示参数是否存在于 `all_matched_args` 内，可用 `Match.available` 判断是否匹配，`Match.result` 获取匹配的值
- `Query`: 查询项，表示参数是否可由 `Arparma.query` 查询并获得结果，可用 `Query.available` 判断是否查询成功，`Query.result` 获取查询结果

**Alconna** 默认依赖注入的目标参数皆不需要使用依赖注入函数， 该效果对于 `AlconnaMatcher.got_path` 下的 Arg 同样有效:

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

如果你更喜欢 Depends 式的依赖注入，`nonebot_plugin_alconna` 同时提供了一系列的依赖注入函数，他们包括：

- `AlconnaResult`: `CommandResult` 类型的依赖注入函数
- `AlconnaMatches`: `Arparma` 类型的依赖注入函数
- `AlconnaDuplication`: `Duplication` 类型的依赖注入函数
- `AlconnaMatch`: `Match` 类型的依赖注入函数，其能够额外传入一个 middleware 函数来处理得到的参数
- `AlconnaQuery`: `Query` 类型的依赖注入函数，其能够额外传入一个 middleware 函数来处理得到的参数
- `AlconnaExecResult`: 提供挂载在命令上的 callback 的返回结果 (`Dict[str, Any]`) 的依赖注入函数
- `AlconnaExtension`: 提供指定类型的 `Extension` 的依赖注入函数

实例:

```python
from nonebot import require
require("nonebot_plugin_alconna")

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


### 跨平台适配

`uniseg` 模块属于 `nonebot-plugin-alconna` 的子插件，其提供了一套通用的消息组件，用于在 `nonebot-plugin-alconna` 下构建通用消息.

#### 通用消息段

适配器下的消息段标注会匹配适配器特定的 `MessageSegment`, 而通用消息段与适配器消息段的区别在于:  

通用消息段会匹配多个适配器中相似类型的消息段，并返回 `uniseg` 模块中定义的 [`Segment` 模型](https://nonebot.dev/docs/next/best-practice/alconna/utils#%E9%80%9A%E7%94%A8%E6%B6%88%E6%81%AF%E6%AE%B5), 以达到**跨平台接收消息**的作用

`uniseg` 模块提供了类似 `MessageSegment` 的通用消息段，并可在 `Alconna` 下直接标注使用：

```python
class Segment:
    """基类标注"""

class Text(Segment):
    """Text对象, 表示一类文本元素"""
    text: str
    style: Optional[str]

class At(Segment):
    """At对象, 表示一类提醒某用户的元素"""
    type: Literal["user", "role", "channel"]
    target: str

class AtAll(Segment):
    """AtAll对象, 表示一类提醒所有人的元素"""

class Emoji(Segment):
    """Emoji对象, 表示一类表情元素"""
    id: str
    name: Optional[str]

class Media(Segment):
    url: Optional[str]
    id: Optional[str]
    path: Optional[str]
    raw: Optional[bytes]

class Image(Media):
    """Image对象, 表示一类图片元素"""

class Audio(Media):
    """Audio对象, 表示一类音频元素"""

class Voice(Media):
    """Voice对象, 表示一类语音元素"""

class Video(Media):
    """Video对象, 表示一类视频元素"""

class File(Segment):
    """File对象, 表示一类文件元素"""
    id: str
    name: Optional[str]

class Reply(Segment):
    """Reply对象，表示一类回复消息"""
    id: str
    """此处不一定是消息ID，可能是其他ID，如消息序号等"""
    msg: Optional[Union[Message, str]]
    origin: Optional[Any]

class Reference(Segment):
    """Reference对象，表示一类引用消息。转发消息 (Forward) 也属于此类"""
    id: Optional[str]
    """此处不一定是消息ID，可能是其他ID，如消息序号等"""
    content: Optional[Union[Message, str, List[Union[RefNode, CustomNode]]]]

class Card(Segment):
    type: Literal["xml", "json"]
    raw: str

class Other(Segment):
    """其他 Segment"""
```
此类消息段通过 `UniMessage.export` 可以转为特定的 `MessageSegment`.


#### 通用信息序列

`uniseg` 模块还提供了一个类似于 `Message` 的 `UniMessage` 类型，其元素为经过通用标注转换后的通用消息段.

你可以通过提供的 `UniversalMessage` 或 `UniMsg` 依赖注入器来获取 `UniMessage`.

```python
from nonebot_plugin_alconna.uniseg import UniMsg, At, Reply


matcher = on_xxx(...)

@matcher.handle()
async def _(msg: UniMsg):
    reply = msg[Reply, 0]
    print(reply.origin)
    if msg.has(At):
        ats = msg.get(At)
        print(ats)
    ...
```

还可以通过 `UniMessage` 的 `export` 与 `send` 方法来**跨平台发送消息**.

```python
from nonebot import Bot, on_command
from nonebot_plugin_alconna.uniseg import Image, UniMessage


test = on_command("test")

@test.handle()
async def handle_test():
    await test.send(await UniMessage(Image(path="path/to/img")).export())
```
`UniMessage.export` 会通过传入的 `bot: Bot` 参数，或上下文中的 `Bot` 对象读取适配器信息，并使用对应的生成方法把通用消息转为适配器对应的消息序列.

而在 `AlconnaMatcher` 下，`got`, `send`, `reject` 等可以发送消息的方法皆支持使用 `UniMessage`，不需要手动调用 export 方法：

```python
from arclet.alconna import Alconna, Args
from nonebot_plugin_alconna import Match, AlconnaMatcher, on_alconna
from nonebot_plugin_alconna.uniseg import At,  UniMessage


test_cmd = on_alconna(Alconna("test", Args["target?", At]))

@test_cmd.handle()
async def tt_h(matcher: AlconnaMatcher, target: Match[At]):
    if target.available:
        matcher.set_path_arg("target", target.result)

@test_cmd.got_path("target", prompt="请输入目标")
async def tt(target: At):
    await test_cmd.send(UniMessage([target, "\ndone."]))
```

除此之外 `UniMessage.send` 方法基于 `UniMessage.export` 并调用各适配器下的发送消息方法，返回一个 `Receipt` 对象，用于修改/撤回消息：

```python
from nonebot import Bot, on_command
from nonebot_plugin_alconna.uniseg import UniMessage


test = on_command("test")

@test.handle()
async def handle():
    receipt = await UniMessage.text("hello!").send(at_sender=True, reply_to=True)
    await receipt.recall(delay=1)
```
**在响应器以外的地方，`bot` 参数必须手动传入**

本插件为以下设配器提供了 **Segment** 标注，可用于匹配各适配器的 `MessageSegment`，也可用于创建 `MessageSegment`:

| 协议名称                                                                | 路径                                   |
|---------------------------------------------------------------------|--------------------------------------|
| [OneBot 协议](https://github.com/nonebot/adapter-onebot)              | adapters.onebot11, adapters.onebot12 |
| [Telegram](https://github.com/nonebot/adapter-telegram)             | adapters.telegram                    |
| [飞书](https://github.com/nonebot/adapter-feishu)                     | adapters.feishu                      |
| [GitHub](https://github.com/nonebot/adapter-github)                 | adapters.github                      |
| [QQ bot](https://github.com/nonebot/adapter-qq)                     | adapters.qq                          |
| [钉钉](https://github.com/nonebot/adapter-ding)                       | adapters.ding                        |
| [Console](https://github.com/nonebot/adapter-console)               | adapters.console                     |
| [开黑啦](https://github.com/Tian-que/nonebot-adapter-kaiheila)         | adapters.kook                        |
| [Mirai](https://github.com/nonebot/adapter-mirai)                   | adapters.mirai, adapters.mirai2      |
| [Ntchat](https://github.com/JustUndertaker/adapter-ntchat)          | adapters.ntchat                      |
| [MineCraft](https://github.com/17TheWord/nonebot-adapter-minecraft) | adapters.minecraft                   |
| [Walle-Q](https://github.com/onebot-walle/nonebot_adapter_walleq)   | adapters.onebot12                    |
| [Discord](https://github.com/nonebot/adapter-discord)               | adapters.discord                     |
| [Red 协议](https://github.com/nonebot/adapter-red)                    | adapters.red                         |
| [Satori](https://github.com/nonebot/adapter-satori)                 | adapters.satori                      |
| [Dodo IM](https://github.com/nonebot/adapter-dodo)                  | adapters.dodo                        |
| [Kritor](https://github.com/nonebot/adapter-kritor)                 | adapters.kritor                      |  
| [Tailchat](https://github.com/eya46/nonebot-adapter-tailchat)       | adapters.tailchat                    |


##### 构造

类比 `Message`, `UniMessage` 可以传入单个字符串/消息段或可迭代的字符串/消息段：

```python
from nonebot_plugin_alconna.uniseg import UniMessage, At


msg = UniMessage("Hello")
msg1 = UniMessage(At("user", "124"))
msg2 = UniMessage(["Hello", At("user", "124")])
```

`UniMessage` 上同时存在便捷方法，令其可以链式地添加消息段：

```python
from nonebot_plugin_alconna.uniseg import UniMessage, At, Image


msg = UniMessage.text("Hello").at("124").image(path="/path/to/img")
assert msg == UniMessage(
    ["Hello", At("user", "124"), Image(path="/path/to/img")]
)
```

##### 拼接消息

`str`、`UniMessage`、`Segment` 对象之间可以直接相加，相加均会返回一个新的 `UniMessage` 对象.

```python
# 消息序列与消息段相加
UniMessage("text") + Text("text")
# 消息序列与字符串相加
UniMessage([Text("text")]) + "text"
# 消息序列与消息序列相加
UniMessage("text") + UniMessage([Text("text")])
# 字符串与消息序列相加
"text" + UniMessage([Text("text")])
# 消息段与消息段相加
Text("text") + Text("text")
# 消息段与字符串相加
Text("text") + "text"
# 消息段与消息序列相加
Text("text") + UniMessage([Text("text")])
# 字符串与消息段相加
"text" + Text("text")
```

如果需要在当前消息序列后直接拼接新的消息段，可以使用 `Message.append`、`Message.extend` 方法，或者使用自加.

```python
msg = UniMessage([Text("text")])
# 自加
msg += "text"
msg += Text("text")
msg += UniMessage([Text("text")])
# 附加
msg.append(Text("text"))
# 扩展
msg.extend([Text("text")])
```

##### 使用消息模板

`UniMessage.template` 同样类似于 `Message.template`，可以用于格式化消息。大体用法参考 [消息模板](https://nonebot.dev/docs/next/tutorial/message#%E4%BD%BF%E7%94%A8%E6%B6%88%E6%81%AF%E6%A8%A1%E6%9D%BF).

这里额外说明 `UniMessage.template` 的拓展控制符.

相比 `Message`，UniMessage 对于 {:XXX} 做了另一类拓展。其能够识别例如 At(xxx, yyy) 或 Emoji(aaa, bbb)的字符串并执行.

以 At(...) 为例使用通用消息段的拓展控制符：

```python
>>> from nonebot_plugin_alconna.uniseg import UniMessage
>>>  UniMessage.template("{:At(user, target)}").format(target="123")
UniMessage(At("user", "123"))
>>> UniMessage.template("{:At(type=user, target=id)}").format(id="123")
UniMessage(At("user", "123"))
>>> UniMessage.template("{:At(type=user, target=123)}").format()
UniMessage(At("user", "123"))
```

而在 `AlconnaMatcher` 中，{:XXX} 更进一步地提供了获取 `event` 和 `bot` 中的属性的功能.

在AlconnaMatcher中使用通用消息段的拓展控制符:

```python
from arclet.alconna import Alconna, Args
from nonebot_plugin_alconna import At, Match, UniMessage, AlconnaMatcher, on_alconna


test_cmd = on_alconna(Alconna("test", Args["target?", At]))

@test_cmd.handle()
async def tt_h(matcher: AlconnaMatcher, target: Match[At]):
    if target.available:
        matcher.set_path_arg("target", target.result)

@test_cmd.got_path(
    "target",
    prompt=UniMessage.template("{:At(user, $event.get_user_id())} 请确认目标")
)
async def tt():
    await test_cmd.send(
      UniMessage.template("{:At(user, $event.get_user_id())} 已确认目标为 {target}")
    )
```
另外也有 `$message_id` 与 `$target` 两个特殊值

##### 检查消息段

我们可以通过 `in` 运算符或消息序列的 `has` 方法来：

```python
# 是否存在消息段
At("user", "1234") in message
# 是否存在指定类型的消息段
At in message
```

我们还可以使用 `only` 方法来检查消息中是否仅包含指定的消息段。

```python
# 是否都为 "test"
message.only("test")
# 是否仅包含指定类型的消息段
message.only(Text)
```

##### 获取消息纯文本

类似于 `Message.extract_plain_text()`，用于获取通用消息的纯文本.
```python 
from nonebot_plugin_alconna.uniseg import UniMessage, At


# 提取消息纯文本字符串
assert UniMessage(
    [At("user", "1234"), "text"]
).extract_plain_text() == "text"
```

##### 遍历

通用消息序列继承自 `List[Segment]` ，因此可以使用 `for` 循环遍历消息段。

```python
for segment in message:  # type: Segment
	...
```

##### 过滤、索引与切片

消息序列对列表的索引与切片进行了增强，在原有列表 `int` 索引与 `slice` 切片的基础上，支持 `type` 过滤索引与切片.

```python
from nonebot_plugin_alconna.uniseg import UniMessage, At, Text, Reply


message = UniMessage(
    [
        Reply(...),
        "text1",
        At("user", "1234"),
        "text2"
    ]
)
# 索引
message[0] == Reply(...)
# 切片
message[0:2] == UniMessage([Reply(...), Text("text1")])
# 类型过滤
message[At] == Message([At("user", "1234")])
# 类型索引
message[At, 0] == At("user", "1234")
# 类型切片
message[Text, 0:2] == UniMessage([Text("text1"), Text("text2")])
```

我们也可以通过消息序列的 `include`、`exclude` 方法进行类型过滤.

```python 
message.include(Text, At)  
message.exclude(Reply)
```

同样的，消息序列对列表的 `index`、`count` 方法也进行了增强，可以用于索引指定类型的消息段.

```python
# 指定类型首个消息段索引
message.index(Text) == 1
# 指定类型消息段数量
message.count(Text) == 2
```

此外，消息序列添加了一个 `get` 方法，可以用于获取指定类型指定个数的消息段.

```python
# 获取指定类型指定个数的消息段
message.get(Text, 1) == UniMessage([Text("test1")])
```

##### 消息发送

通用消息可用 `UniMessage.send` 发送自身：

```python
async def send(
    self,
    target: Union[Event, Target, None] = None,
    bot: Optional[Bot] = None,
    fallback: bool = True,
    at_sender: Union[str, bool] = False,
    reply_to: Union[str, bool] = False,
) -> Receipt:
```

实际上，`UniMessage` 同时提供了获取消息事件 id 与消息发送对象的方法:

```python
from nonebot import Event, Bot
from nonebot_plugin_alconna.uniseg import Target, get_message_id, get_target


matcher = on_xxx(...)

@matcher.handle()
async def _(bot: Bot, event: Event):
    target: Target = get_target(event, bot)
    msg_id: str = get_message_id(event, bot)

```

`send`, `get_target`, `get_message_id` 中与 `event`, `bot` 相关的参数都会尝试从上下文中获取对象.

其中，`Target`:

```python
class Target:
    id: str
    """目标id；若为群聊则为group_id或者channel_id，若为私聊则为user_id"""
    parent_id: str = ""
    """父级id；若为频道则为guild_id，其他情况为空字符串"""
    channel: bool = False
    """是否为频道，仅当目标平台同时支持群聊和频道时有效"""
    private: bool = False
    """是否为私聊"""
    source: str = ""
    """可能的事件id"""
```
是用来描述响应消息时的发送对象.

同样的，你可以通过依赖注入的方式在响应器中直接获取它们.

#### 按钮回调

`on_button` 用于响应指定 id 的按钮回调，不传入 id 时响应所有按钮:

```python
from nonebot import require

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna import Button, ButtonCallback, Keyboard, Text, UniMessage, on_alconna, on_button

menu = on_alconna("button-demo")


@menu.handle()
async def send_menu():
    await (
        UniMessage(Text("请选择操作").markdown())
        + Keyboard(buttons=[Button("action", "确认", id="demo.confirm", text="confirmed")], row=1)
    ).send()


confirmed = on_button("demo.confirm")


@confirmed.handle()
async def handle_confirm(interaction: ButtonCallback):
    await UniMessage("已确认").send(target=interaction.event, bot=interaction.bot)
```

`ButtonCallback` 提供以下属性:

- `bot`: 当前 Bot
- `event`: 原始事件
- `id`: 按钮 id
- `data`: 按钮回调数据，Telegram 与 `id` 相同，Discord 为 `None`
- `user_id`: 点击按钮的用户 id

目前支持 QQ-API、Telegram 和 Discord。按钮回调会自动应答，无需在响应函数中再次处理。

### 条件控制

本插件可以通过 `assign` 来控制一个具体的响应函数是否在不满足条件时跳过响应

```python
from nonebot import require  
require("nonebot_plugin_alconna")  
...  
  
from arclet.alconna import Alconna, Subcommand, Option, Args  
from nonebot_plugin_alconna import on_alconna, CommandResult  
  
pip = Alconna(  
"pip",  
Subcommand(  
"install", Args["pak", str],  
Option("--upgrade"),  
Option("--force-reinstall")  
),  
Subcommand("list", Option("--out-dated"))  
)  
  
pip_cmd = on_alconna(pip)  
  
# 仅在命令为 `pip install pip` 时响应  
@pip_cmd.assign("install.pak", "pip")  
async def update(res: CommandResult):  
...  
  
# 仅在命令为 `pip list` 时响应  
@pip_cmd.assign("list")  
async def list_(res: CommandResult):  
...  
  
# 在命令为 `pip install xxx` 时响应  
@pip_cmd.assign("install")  
async def install(res: CommandResult):  
...
```


### 响应器创建装饰

本插件提供了一个 `funcommand` 装饰器, 其用于将一个接受任意参数， 返回 `str` 或 `Message` 或 `MessageSegment` 的函数转换为命令响应器.

```python
from nonebot_plugin_alconna import funcommand


@funcommand()
async def echo(msg: str):
    return msg
```

其等同于

```python
from arclet.alconna import Alconna, Args
from nonebot_plugin_alconna import on_alconna, AlconnaMatch, Match


echo = on_alconna(Alconna("echo", Args["msg", str]))

@echo.handle()
async def echo_exit(msg: Match[str] = AlconnaMatch("msg")):
    await echo.finish(msg.result)

```

### 类Koishi构造器

本插件提供了一个 `Command` 构造器，其基于 `arclet.alconna.tools` 中的 `AlconnaString`， 以类似 `Koishi` 中注册命令的方式来构建一个 **AlconnaMatcher** :

```python
from nonebot_plugin_alconna import Command, Arparma


book = (
    Command("book", "测试")
    .option("writer", "-w <id:int>")
    .option("writer", "--anonymous", {"id": 0})
    .usage("book [-w <id:int> | --anonymous]")
    .shortcut("测试", {"args": ["--anonymous"]})
    .build()
)

@book.handle()
async def _(arp: Arparma):
    await book.send(str(arp.options))
```

甚至，你可以设置 `action` 来设定响应行为：

```python
book = (
    Command("book", "测试")
    .option("writer", "-w <id:int>")
    .option("writer", "--anonymous", {"id": 0})
    .usage("book [-w <id:int> | --anonymous]")
    .shortcut("测试", {"args": ["--anonymous"]})
    .action(lambda options: str(options))  # 会自动通过 bot.send 发送
    .build()
)
```

### 返回值回调

在 `AlconnaMatch`, `AlconnaQuery` 或 `got_path` 中，你可以使用 `middleware` 参数来传入一个对返回值进行处理的函数:

```python
from nonebot_plugin_alconna import image_fetch


mask_cmd = on_alconna(
    Alconna("search", Args["img?", Image]),
)


@mask_cmd.handle()
async def mask_h(matcher: AlconnaMatcher, img: Match[bytes] = AlconnaMatch("img", image_fetch)):
    result = await search_img(img.result)
    await matcher.send(result.content)
```

其中，`image_fetch` 是一个中间件，其接受一个 `Image` 对象，并提取图片的二进制数据返回.


### 匹配拓展

本插件提供了一个 `Extension` 类，其用于自定义 AlconnaMatcher 的部分行为.

例如 `LLMExtension` (仅举例)：

```python
from nonebot_plugin_alconna import Extension, Alconna, on_alconna, Interface


class LLMExtension(Extension):
    @property
    def priority(self) -> int:
        return 10

    @property
    def id(self) -> str:
        return "LLMExtension"

    def __init__(self, llm):
      self.llm = llm

    def post_init(self, alc: Alconna) -> None:
        self.llm.add_context(alc.command, alc.meta.description)

    async def receive_wrapper(self, bot, event, receive):
        resp = await self.llm.input(str(receive))
        return receive.__class__(resp.content)

    def before_catch(self, name, annotation, default):
        return name == "llm"

    def catch(self, interface: Interface):
        if interface.name == "llm":
            return self.llm

matcher = on_alconna(
    Alconna(...),
    extensions=[LLMExtension(LLM)]
)
...
```

那么添加了 `LLMExtension` 的响应器便能接受任何能通过 llm 翻译为具体命令的自然语言消息，同时可以在响应器中为所有 `llm` 参数注入模型变量

目前 `Extension` 的功能有:

- `validate`: 对于事件的来源适配器或 bot 选择是否接受响应
- `output_converter`: 输出信息的自定义转换方法
- `message_provider`: 从传入事件中自定义提取消息的方法
- `receive_provider`: 对传入的消息 (Message 或 UniMessage) 的额外处理
- `permission_check`: 命令对消息解析并确认头部匹配（即确认选择响应）时对发送者的权限判断
- `parse_wrapper`: 对命令解析结果的额外处理
- `send_wrapper`: 对发送的消息 (Message 或 UniMessage) 的额外处理
- `before_catch`: 自定义依赖注入的绑定确认函数
- `catch`: 自定义依赖注入处理函数
- `post_init`: 响应器创建后对命令对象的额外处理

例如内置的 `DiscordSlashExtension`，其可自动将 Alconna 对象翻译成 slash 指令并注册，且将收到的指令交互事件转为指令供命令解析:

```python
from nonebot_plugin_alconna import Match, on_alconna
from nonebot_plugin_alconna.adapters.discord import DiscordSlashExtension


alc = Alconna(
    ["/"],
    "permission",
    Subcommand("add", Args["plugin", str]["priority?", int]),
    Option("remove", Args["plugin", str]["time?", int]),
    meta=CommandMeta(description="权限管理"),
)

matcher = on_alconna(alc, extensions=[DiscordSlashExtension()])

@matcher.assign("add")
async def add(plugin: Match[str], priority: Match[int]):
    await matcher.finish(f"added {plugin.result} with {priority.result if priority.available else 0}")

@matcher.assign("remove")
async def remove(plugin: Match[str], time: Match[int]):
    await matcher.finish(f"removed {plugin.result} with {time.result if time.available else -1}")
```

TIP:  
全局的 Extension 可延迟加载 (即若有全局拓展加载于部分 AlconnaMatcher 之后，这部分响应器会被追加拓展)


## 本体
[`Alconna`](https://github.com/ArcletProject/Alconna) 隶属于 `ArcletProject`，是一个简单、灵活、高效的命令参数解析器, 并且不局限于解析命令式字符串.

我们通过一个例子来讲解 **Alconna** 的核心: `Args`, `Subcommand`, `Option`:

```python
from arclet.alconna import Alconna, Args, Subcommand, Option


alc = Alconna(
    "pip",
    Subcommand(
        "install",
        Args["package", str],
        Option("-r|--requirement", Args["file", str]),
        Option("-i|--index-url", Args["url", str]),
    )
)

res = alc.parse("pip install nonebot2 -i URL")

print(res)
# matched=True, header_match=(origin='pip' result='pip' matched=True groups={}), subcommands={'install': (value=Ellipsis args={'package': 'nonebot2'} options={'index-url': (value=None args={'url': 'URL'})} subcommands={})}, other_args={'package': 'nonebot2', 'url': 'URL'} 

print(res.all_matched_args)
# {'package': 'nonebot2', 'url': 'URL'}
```

这段代码通过`Alconna`创捷了一个接受主命令名为`pip`, 子命令为`install`且子命令接受一个 **Args** 参数`package`和二个 **Option** 参数`-r`和`-i`的命令参数解析器, 通过`parse`方法返回解析结果 **Arparma** 的实例.


### 组成

#### 命令头
命令头是指命令的前缀 (Prefix) 与命令名 (Command) 的组合，例如 !help 中的 ! 与 help.
|前缀|命令名|匹配内容|说明|
|:-:|:-:|:-:|:-:|
|-|"foo"|`"foo"`|无前缀的纯文字头|
|-|123|`123`|无前缀的元素头|
|-|"re:\d{2}"|`"32"`|无前缀的正则头|
|-|int|`123` 或 `"456"`|无前缀的类型头|
|[int, bool]|-|`True` 或 `123`|无名的元素类头|
|["foo", "bar"]|-|`"foo"` 或 `"bar"`|无名的纯文字头|
|["foo", "bar"]|"baz"|`"foobaz"` 或 `"barbaz"`|纯文字头|
|[int, bool]|"foo"|`[123, "foo"]` 或 `[False, "foo"]`|类型头|
|[123, 4567]|"foo"|`[123, "foo"]` 或 `[4567, "foo"]`|元素头|
|[nepattern.NUMBER]|"bar"|`[123, "bar"]` 或 `[123.456, "bar"]`|表达式头|
|[123, "foo"]|"bar"|`[123, "bar"]` 或 `"foobar"` 或 `["foo", "bar"]`|混合头|
|[(int, "foo"), (456, "bar")]|"baz"|`[123, "foobaz"]` 或 `[456, "foobaz"]` 或 `[456, "barbaz"]`|对头|

无前缀的类型头：此时会将传入的值尝试转为 BasePattern，例如 `int` 会转为 `nepattern.INTEGER`。此时命令头会匹配对应的类型， 例如 `int` 会匹配 `123` 或 `"456"`，但不会匹配 `"foo"`。同时，Alconna 会将命令头匹配到的值转为对应的类型，例如 `int` 会将 `"123"` 转为 `123`。

**正则只在命令名上生效，命令前缀中的正则会被转义**  
除了通过传入 `re:xxx` 来使用正则表达式外，Alconna 还提供了一种更加简洁的方式来使用正则表达式，那就是 Bracket Header。

```python
from alconna import Alconna


alc = Alconna(".rd{roll:int}")
assert alc.parse(".rd123").header["roll"] == 123
```

Bracket Header 类似 python 里的 f-string 写法，通过 "{}" 声明匹配类型

"{}" 中的内容为 "name:type or pat"：
- "{}", "{:}" **⇔** "(.+)", 占位符
- "{foo}" **⇔** "(?P&lt;foo&gt;.+)"
- "{:\d+}" **⇔** "(\d+)"
- "{foo:int}" **⇔** "(?P&lt;foo&gt;\d+)"，其中 "int" 部分若能转为 `BasePattern` 则读取里面的表达式


#### 参数声明(Args)

`Args` 是用于声明命令参数的组件, 可以通过以下几种方式构造 **Args** :

 - `Args[key, var, default][key1, var1, default1][...]` 
 - `Args[(key, var, default)]`
 - `Args.key[var, default]`
 
其中，key **一定**是字符串，而 var 一般为参数的类型，default 为具体的值或者 **arclet.alconna.args.Field**.

其与函数签名类似，但是允许含有默认值的参数在前；同时支持 keyword-only 参数不依照构造顺序传入 （但是仍需要在非 keyword-only 参数之后）.

##### key
`key` 的作用是用以标记解析出来的参数并存放于 **Arparma** 中，以方便用户调用.

其有三种为 Args 注解的标识符:  `?`、`/`、 `!`, 标识符与 key 之间建议以 `;` 分隔:

- `!` 标识符表示该处传入的参数应**不是**规定的类型，或**不在**指定的值中。
- `?` 标识符表示该参数为**可选**参数，会在无参数匹配时跳过。
- `/` 标识符表示该参数的类型注解需要隐藏。

另外，对于参数的注释也可以标记在 `key` 中，其与 key 或者标识符 以 `#` 分割：  
`foo#这是注释;?` 或 `foo?#这是注释`

`Args` 中的 `key` 在实际命令中并不需要传入（keyword 参数除外）：

```python
from arclet.alconna import Alconna, Args  


alc = Alconna("test", Args["foo", str])  
alc.parse("test --foo abc") # 错误  
alc.parse("test abc") # 正确
```

若需要 `test --foo abc`，你应该使用 `Option`：

```python
from arclet.alconna import Alconna, Args, Option


alc = Alconna("test", Option("--foo", Args["foo", str]))
```
##### var
var 负责命令参数的**类型检查**与**类型转化**.

`Args` 的`var`表面上看需要传入一个 `type`，但实际上它需要的是一个 `nepattern.BasePattern` 的实例.

```python
from arclet.alconna import Args  
from nepattern import BasePattern  


# 表示 foo 参数需要匹配一个 @number 样式的字符串  
args = Args["foo", BasePattern("@\d+")]
```

示例中可以传入 `str` 是因为 `str` 已经注册在了 `nepattern.global_patterns` 中，因此会替换为 `nepattern.global_patterns[str]`.

`nepattern.global_patterns`默认支持的类型有：

- `str`: 匹配任意字符串
- `int`: 匹配整数
- `float`: 匹配浮点数
- `bool`: 匹配 `True` 与 `False` 以及他们小写形式
- `hex`: 匹配 `0x` 开头的十六进制字符串
- `url`: 匹配网址
- `email`: 匹配 `xxxx@xxx` 的字符串
- `ipv4`: 匹配 `xxx.xxx.xxx.xxx` 的字符串
- `list`: 匹配类似 `["foo","bar","baz"]` 的字符串
- `dict`: 匹配类似 `{"foo":"bar","baz":"qux"}` 的字符串
- `datetime`: 传入一个 `datetime` 支持的格式字符串，或时间戳
- `Any`: 匹配任意类型
- `AnyString`: 匹配任意类型，转为 `str`
- `Number`: 匹配 `int` 与 `float`，转为 `int`

同时可以使用 typing 中的类型：

- `Literal[X]`: 匹配其中的任意一个值
- `Union[X, Y]`: 匹配其中的任意一个类型
- `Optional[xxx]`: 会自动将默认值设为 `None`，并在解析失败时使用默认值
- `List[X]`: 匹配一个列表，其中的元素为 `X` 类型
- `Dict[X, Y]`: 匹配一个字典，其中的 key 为 `X` 类型，value 为 `Y` 类型
- ...

几类特殊的传入标记：

- `"foo"`: 匹配字符串 "foo" (若没有某个 `BasePattern` 与之关联)
- `RawStr("foo")`: 匹配字符串 "foo" (不会被 `BasePattern` 替换)
- `"foo|bar|baz"`: 匹配 "foo" 或 "bar" 或 "baz"
- `[foo, bar, Baz, ...]`: 匹配其中的任意一个值或类型
- `Callable[[X], Y]`: 匹配一个参数为 `X` 类型的值，并返回通过该函数调用得到的 `Y` 类型的值
- `"re:xxx"`: 匹配一个正则表达式 `xxx`，会返回 Match[0]
- `"rep:xxx"`: 匹配一个正则表达式 `xxx`，会返回 `re.Match` 对象
- `{foo: bar, baz: qux}`: 匹配字典中的任意一个键, 并返回对应的值 (特殊的键 ... 会匹配任意的值)
- ...

`MultiVar` 则是一个特殊的标注，用于告知解析器该参数可以接受多个值，其构造方法形如 `MultiVar(str)`。 同样的还有 `KeyWordVar`，其构造方法形如 `KeyWordVar(str)`，用于告知解析器该参数为一个 keyword-only 参数.

TIPS:

`MultiVar` 与 `KeyWordVar` 组合时，代表该参数为一个可接受多个 key-value 的参数，其构造方法形如 `MultiVar(KeyWordVar(str))`.

`MultiVar` 与 `KeyWordVar` 也可以传入 `default` 参数，用于指定默认值.

`MultiVar` 不能在 `KeyWordVar` 之后传入.


#### **Option** 和 **Subcommand**
`Option` 可以传入一组 `alias`，如 `Option("--foo|-F|--FOO|-f")` 或 `Option("--foo", alias=["-F"]`.  

传入别名后，`option` 会选择其中长度最长的作为选项名称。若传入为 "--foo|-f"，则命令名称为 "--foo".  

**在 Alconna 中 Option 的名字或别名**没有要求**必须在前面写上 `-`.**  

`Subcommand` 可以传入自己的 **Option** 与 **Subcommand**.  

他们拥有如下共同参数:

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


`Option` 可以特别设置传入一类 `Action`，作为解析操作.

`Action` 分为三类:

- `store`: 无 Args 时， 仅存储一个值， 默认为 Ellipsis； 有 Args 时， 后续的解析结果会覆盖之前的值
- `append`: 无 Args 时， 将多个值存为列表， 默认为 Ellipsis； 有 Args 时， 每个解析结果会追加到列表中, 当存在默认值并且不为列表时， 会自动将默认值变成列表， 以保证追加的正确性
- `count`: 无 Args 时， 计数器加一； 有 Args 时， 表现与 STORE 相同, 当存在默认值并且不为数字时， 会自动将默认值变成 1， 以保证计数器的正确性。

`Alconna` 提供了预制的几类 `Action`：

- `store`(默认)，`store_value`，`store_true`，`store_false`
- `append`，`append_value`
- `count`


#### Arparma

`Alconna.parse` 会返回由 **Arparma** 承载的解析结果.

`Arparma` 会有如下参数：

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

`path` 支持如下:
- `main_args`, `options`, ...: 返回对应的属性
- `args`: 返回 all_matched_args
- `main_args.xxx`, `options.xxx`, ...: 返回字典中 `xxx`键对应的值
- `args.xxx`: 返回 all_matched_args 中 `xxx`键对应的值
- `options.foo`, `foo`: 返回选项 `foo` 的解析结果 (OptionResult)
- `options.foo.value`, `foo.value`: 返回选项 `foo` 的解析值
- `options.foo.args`, `foo.args`: 返回选项 `foo` 的解析参数字典
- `options.foo.args.bar`, `foo.bar`: 返回选项 `foo` 的参数字典中 `bar` 键对应的值 ...


### 命名空间配置

命名空间配置 (以下简称命名空间) 相当于`Alconna`的设置，`Alconna`默认使用"Alconna"命名空间，命名空间有以下几个属性:

- name: 命名空间名称
- prefixes: 默认前缀配置
- separators: 默认分隔符配置
- formatter_type: 默认格式化器类型
- fuzzy_match: 默认是否开启模糊匹配
- raise_exception: 默认是否抛出异常
- builtin_option_name: 默认的内置选项名称(--help, --shortcut, --comp)
- enable_message_cache: 默认是否启用消息缓存
- compact: 默认是否开启紧凑模式
- strict: 命令是否严格匹配
- ...

#### 新建命名空间并替换
```python
from arclet.alconna import Alconna, namespace, Namespace, Subcommand, Args, config


ns = Namespace("foo", prefixes=["/"])  # 创建 "foo"命名空间配置, 它要求创建的Alconna的主命令前缀必须是/

alc = Alconna("pip", Subcommand("install", Args["package", str]), namespace=ns) # 在创建Alconna时候传入命名空间以替换默认命名空间

# 可以通过with方式创建命名空间
with namespace("bar") as np1:
    np1.prefixes = ["!"]    # 以上下文管理器方式配置命名空间，此时配置会自动注入上下文内创建的命令
    np1.formatter_type = ShellTextFormatter  # 设置此命名空间下的命令的 formatter 默认为 ShellTextFormatter
    np1.builtin_option_name["help"] = {"帮助", "-h"}  # 设置此命名空间下的命令的帮助选项名称

# 你还可以使用config来管理所有命名空间并切换至任意命名空间
config.namespaces["foo"] = ns  # 将命名空间挂载到 config 上

alc = Alconna("pip", Subcommand("install", Args["package", str]), namespace=config.namespaces["foo"]) # 也是同样可以切换到"foo"命名空间
```


#### 修改默认的命名空间
```python
from arclet.alconna import config, namespace, Namespace


config.default_namespace.prefixes = [...]  # 直接修改默认配置

np = Namespace("xxx", prefixes=[...])
config.default_namespace = np  # 更换默认的命名空间

with namespace(config.default_namespace.name) as np:
    np.prefixes = [...]
```


### 快捷指令

快捷命令可以做到标识一段命令, 并且传递参数给原命令.

一般情况下你可以通过 `Alconna.shortcut` 进行快捷指令操作 (创建，删除)

`shortcut` 的第一个参数为快捷指令名称，第二个参数为 `ShortcutArgs`，作为快捷指令的配置.

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

#### args的使用

```python
from arclet.alconna import Alconna, Args


alc = Alconna("setu", Args["count", int])

alc.shortcut("涩图(\d+)张", {"args": ["{0}"]})
# 'Alconna::setu 的快捷指令: "涩图(\\d+)张" 添加成功'

alc.parse("涩图3张").query("count")
# 3
```

#### command的使用

```python
from arclet.alconna import Alconna, Args


alc = Alconna("eval", Args["content", str])

alc.shortcut("echo", {"command": "eval print(\\'{*}\\')"})
# 'Alconna::eval 的快捷指令: "echo" 添加成功'

alc.shortcut("echo", delete=True) # 删除快捷指令
# 'Alconna::eval 的快捷指令: "echo" 删除成功'

@alc.bind() # 绑定一个命令执行器, 若匹配成功则会传入参数, 自动执行命令执行器
def cb(content: str):
    eval(content, {}, {})

alc.parse('eval print(\\"hello world\\")')
# hello world

alc.parse("echo hello world!")
# hello world!
```

当 `fuzzy` 为 False 时，第一个例子中传入 `"涩图1张 abc"` 之类的快捷指令将视为解析失败

快捷指令允许三类特殊的 placeholder:

- `{%X}`: 如 `setu {%0}`，表示此处填入快捷指令后随的第 X 个参数。

例如，若快捷指令为 `涩图`, 配置为 `{"command": "setu {%0}"}`, 则指令 `涩图 1` 相当于 `setu 1`

- `{*}`: 表示此处填入所有后随参数，并且可以通过 `{*X}` 的方式指定组合参数之间的分隔符。

- `{X}`: 表示此处填入可能的正则匹配的组：

- 若 `command` 中存在匹配组 `(xxx)`，则 `{X}` 表示第 X 个匹配组的内容
- 若 `command` 中存储匹配组 `(?P<xxx>...)`, 则 `{X}` 表示 **名字** 为 X 的匹配结果

除此之外, 通过 **Alconna** 内置选项 `--shortcut` 可以动态操作快捷指令.

例如:
- `cmd --shortcut <key> <cmd>` 来增加一个快捷指令
- `cmd --shortcut list` 来列出当前指令的所有快捷指令
- `cmd --shortcut delete key` 来删除一个快捷指令

```python
from arclet.alconna import Alconna, Args


alc = Alconna("eval", Args["content", str])

alc.shortcut("echo", {"command": "eval print(\\'{*}\\')"})

alc.parse("eval --shortcut list")
# 'echo'
```

### 紧凑命令
`Alconna`, `Option` 与 `Subcommand` 可以设置 `compact=True` 使得解析命令时允许名称与后随参数之间没有分隔:

```python
from arclet.alconna import Alconna, Option, CommandMeta, Args


alc = Alconna("test", Args["foo", int], Option("BAR", Args["baz", str], compact=True), meta=CommandMeta(compact=True))

assert alc.parse("test123 BARabc").matched
```

这使得我们可以实现如下命令：

```python
from arclet.alconna import Alconna, Option, Args, append


alc = Alconna("gcc", Option("--flag|-F", Args["content", str], action=append, compact=True))
print(alc.parse("gcc -Fabc -Fdef -Fxyz").query[list]("flag.content"))
# ['abc', 'def', 'xyz']
```

当 `Option` 的 `action` 为 `count` 时，其自动支持 `compact` 特性：

```python
from arclet.alconna import Alconna, Option, count


alc = Alconna("pp", Option("--verbose|-v", action=count, default=0))
print(alc.parse("pp -vvv").query[int]("verbose.value"))
# 3
```


### 模糊匹配

模糊匹配通过在 Alconna 中设置其 CommandMeta 开启。

模糊匹配会应用在任意需要进行名称判断的地方，如 **命令名称**，**选项名称** 和 **参数名称** (如指定需要传入参数名称).

```python
from arclet.alconna import Alconna, CommandMeta


alc = Alconna("test_fuzzy", meta=CommandMeta(fuzzy_match=True))

alc.parse("test_fuzy")
# test_fuzy is not matched. Do you mean "test_fuzzy"?
```


### 半自动补全

半自动补全为用户提供了推荐后续输入的功能。

补全默认通过 `--comp` 或 `-cp` 或 `?` 触发：（命名空间配置可修改名称）

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


### Duplication

**Duplication** 用来提供更好的自动补全，类似于 **ArgParse** 的 **Namespace**.

普通情况下使用，需要利用到 **ArgsStub**、**OptionStub** 和 **SubcommandStub** 三个部分，

以pip为例，其对应的 Duplication 应如下构造:

```python
from arclet.alconna import Alconna, Args, Option, OptionResult, Duplication, SubcommandStub, Subcommand, count


class MyDup(Duplication):
    verbose: OptionResult
    install: SubcommandStub


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

res = alc.parse("pip -v install ...") # 不使用duplication获得的提示较少
print(res.query("install"))
# (value=Ellipsis args={'package': '...'} options={} subcommands={})

result = alc.parse("pip -v install ...", duplication=MyDup)
print(result.install)
# SubcommandStub(_origin=Subcommand('install', args=Args('package': str)), _value=Ellipsis, available=True, args=ArgsStub(_origin=Args('package': str), _value={'package': '...'}, available=True), dest='install', options=[OptionStub(_origin=Option('requirement', args=Args('file': str)), _value=None, available=False, args=ArgsStub(_origin=Args('file': str), _value={}, available=False), dest='requirement', aliases=['r', 'requirement'], name='requirement'), OptionStub(_origin=Option('index-url', args=Args('url': str)), _value=None, available=False, args=ArgsStub(_origin=Args('url': str), _value={}, available=False), dest='index-url', aliases=['index-url', 'i'], name='index-url')], subcommands=[], name='install')
```

**Duplication** 也可以如 **Namespace** 一样直接标明参数名称和类型:
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
