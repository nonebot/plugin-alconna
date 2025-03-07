<p align="center">
  <a href="https://nonebot.dev/docs/next/best-practice/alconna/"><img src="https://v2.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>

<div align="center">

# NoneBot Plugin Alconna

_✨ Alconna Usage For NoneBot2 ✨_

_✨ All Receive in One, And One Send All ✨_

</div>

<p align="center">
  <a href="https://raw.githubusercontent.com/nonebot/plugin-alconna/master/LICENSE">
    <img src="https://img.shields.io/github/license/nonebot/plugin-alconna.svg" alt="license">
  </a>
  <a href="https://pypi.python.org/pypi/nonebot-plugin-alconna">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-alconna.svg" alt="pypi">
  </a>
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">
</p>

该插件提供了 [Alconna](https://github.com/ArcletProject/Alconna) 的 [NoneBot2](https://github.com/nonebot/nonebot2) 适配版本与工具

## 特性

- 完整的 Alconna 特性支持
- 自动回复命令帮助信息选项
- 跨平台的接收与发送消息(被动+主动)
- 对**20种适配器**的收发消息支持
- 比 `got-reject` 更强大的补全会话机制
- 多种内置插件 (echo，help，lang)
- i18n 支持

## 讨论

QQ 交流群: [链接](https://jq.qq.com/?_wv=1027&k=PUPOnCSH)


## 使用方法

NoneBot 文档: [📖这里](https://nonebot.dev/docs/next/best-practice/alconna/)
仓库内介绍: [📦这里](/docs.md)

## 跨平台消息

```python
from nonebot import get_driver
from nonebot_plugin_alconna import Target, UniMessage, SupportScope, on_alconna

driver = get_driver()
test = on_alconna("test")

@test.handle()
async def handle_test():
    r = await UniMessage.image(path="path/to/img").send()
    if r.recallable:
        await r.reply("图片已发送，10秒后撤回")
        await r.recall(delay=10, index=0)

@test.got("foo", prompt=UniMessage.template("{:Reply($message_id)}请输入图片"))
async def handle_foo():
    await test.send("图片已收到")

@driver.on_startup
async def _():
    await Target.group("123456789", SupportScope.qq_client).send(UniMessage.image(path="test.png"))
```

## 支持情况

### 支持的适配器

| 协议名称                                                                | 路径                                   |
|---------------------------------------------------------------------|--------------------------------------|
| [OneBot 协议](https://onebot.dev/)                                    | adapters.onebot11, adapters.onebot12 |
| [Telegram](https://core.telegram.org/bots/api)                      | adapters.telegram                    |
| [飞书](https://open.feishu.cn/document/home/index)                    | adapters.feishu                      |
| [GitHub](https://docs.github.com/en/developers/apps)                | adapters.github                      |
| [QQ bot](https://github.com/nonebot/adapter-qq)                     | adapters.qq                          |
| [钉钉](https://open.dingtalk.com/document/)                           | adapters.ding                        |
| [Console](https://github.com/nonebot/adapter-console)               | adapters.console                     |
| [开黑啦](https://developer.kookapp.cn/)                                | adapters.kook                        |
| [Mirai](https://docs.mirai.mamoe.net/mirai-api-http/)               | adapters.mirai                       |
| [Ntchat](https://github.com/JustUndertaker/adapter-ntchat)          | adapters.ntchat                      |
| [MineCraft](https://github.com/17TheWord/nonebot-adapter-minecraft) | adapters.minecraft                   |
| [Walle-Q](https://github.com/onebot-walle/nonebot_adapter_walleq)   | adapters.onebot12                    |
| [Discord](https://github.com/nonebot/adapter-discord)               | adapters.discord                     |
| [Red 协议](https://github.com/nonebot/adapter-red)                    | adapters.red                         |
| [Satori](https://github.com/nonebot/adapter-satori)                 | adapters.satori                      |
| [Dodo IM](https://github.com/nonebot/adapter-dodo)                  | adapters.dodo                        |
| [Kritor](https://github.com/nonebot/adapter-kritor)                 | adapters.kritor                      |
| [Tailchat](https://github.com/eya46/nonebot-adapter-tailchat)       | adapters.tailchat                    |
| [Mail](https://github.com/mobyw/nonebot-adapter-mail)               | adapters.mail                        |
| [微信公众号](https://github.com/YangRucheng/nonebot-adapter-wxmp)        | adapters.wxmp                        |
| [黑盒语音](https://github.com/lclbm/adapter-heybox)                     | adapters.heybox                      |

### 支持的消息元素

- ✅: 支持(接收和发送)
- ⬇️: 支持接收
- ⬆️: 支持发送
- ➖: 情况不存在
- ❌: 插件未支持
- 🚫: 协议未支持
- (🚧): 计划中或部分支持或为实验性支持

> [!WARNING]
> 斜体的协议名称意味着其协议或其适配器长时间未维护或已失效

| 元素\适配器           | OneBot V11 | OneBot V12 | Telegram | 飞书 | Github | QQ-API | _钉钉_ | Console | 开黑啦 | Mirai | _Ntchat_ | MineCraft | Discord | _Red_ | Satori | Dodo IM | Kritor | Tailchat | Mail | 微信公众号 | 黑盒语音 |
|------------------|------------|------------|----------|----|--------|--------|------|---------|-----|-------|----------|-----------|---------|-------|--------|---------|--------|----------|------|-------|------|
| 文本 Text          | ✅          | ✅          | ✅        | ✅  | ✅      | ✅      | ✅    | ✅       | ✅   | ✅     | ✅        | ✅         | ✅       | ✅     | ✅      | ✅       | ✅      | ✅        | ✅    | ✅     | ✅    |
| 样式文本 Styled Text | 🚫         | 🚫         | ✅        | 🚫 | ✅      | ✅      | ❌    | ✅       | ✅   | 🚫    | 🚫       | ✅         | 🚫      | 🚫    | ✅      | 🚫      | 🚫     | ✅        | ✅    | 🚫    | 🚫   | 
| 提及用户 At(user)    | ✅          | ✅          | ✅        | ✅  | ⬆️     | ✅      | ✅    | 🚫      | ✅   | ✅     | ❌        | 🚫        | ✅       | ✅     | ✅      | ✅       | ✅      | ✅        | ⬆️   | 🚫    | ⬆️   |
| 提及角色 At(role)    | 🚫         | 🚫         | 🚫       | 🚫 | 🚫     | 🚫     | 🚫   | 🚫      | ✅   | 🚫    | 🚫       | 🚫        | ✅       | 🚫    | ✅      | ✅       | 🚫     | 🚫       | 🚫   | 🚫    | 🚫   |
| 提及频道 At(channel) | 🚫         | 🚫         | 🚫       | 🚫 | 🚫     | ✅      | 🚫   | 🚫      | ✅   | 🚫    | 🚫       | 🚫        | ✅       | 🚫    | ✅      | ✅       | 🚫     | ✅        | ⬆️   | 🚫    | 🚫   |
| 提交全体 AtAll       | ✅          | ✅          | 🚫       | ✅  | 🚫     | ✅      | ✅    | 🚫      | ✅   | ✅     | 🚫       | 🚫        | ✅       | ✅     | ✅      | ✅       | ✅      | 🚫       | 🚫   | 🚫    | 🚫   | 
| 表情 Emoji         | ✅          | 🚫         | ✅        | 🚫 | 🚫     | ✅      | 🚫   | ✅       | ✅   | ✅     | 🚫       | 🚫        | ✅       | ✅     | 🚫     | 🚫      | ✅      | ✅        | 🚫   | ✅     | 🚫   |
| 图片 Image         | ✅          | ✅          | ✅        | ✅  | ⬆️     | ✅      | ✅    | 🚫      | ✅   | ✅     | ✅        | ❌         | ✅       | ✅     | ✅      | ✅       | ✅      | ✅        | ✅    | ✅     | ⬆️   |
| 音频 Audio         | ⬆️         | ✅          | ✅        | ✅  | 🚫     | ✅      | 🚫   | 🚫      | ✅   | ⬆️    | ⬇️       | 🚫        | ⬆️      | ⬆️    | ✅      | 🚫      | ⬆️     | 🚫       | ✅    | ✅     | 🚫   |
| 语音 Voice         | ✅          | ✅          | ✅        | ⬆️ | 🚫     | ⬆️     | 🚫   | 🚫      | ⬆️  | ✅     | ⬇️       | 🚫        | ⬆️      | ✅     | ⬆️     | 🚫      | ✅      | 🚫       | ✅    | ✅     | 🚫   |
| 视频 Video         | ✅          | ✅          | ✅        | ✅  | 🚫     | ✅      | 🚫   | 🚫      | ✅   | ✅     | ✅        | 🚫        | ⬆️      | ✅     | ✅      | ✅       | ✅      | 🚫       | ✅    | ✅     | 🚫   |
| 文件 File          | ⬇️,⬆️(🚧)  | ✅          | ✅        | ✅  | 🚫     | ✅      | 🚫   | 🚫      | ✅   | ✅     | ✅        | 🚫        | ⬆️      | ✅     | ✅      | ⬇️      | ⬇️     | ✅        | ✅    | 🚫    | 🚫   |
| 回复 Reply         | ✅          | ✅          | ✅        | ✅  | 🚫     | ✅      | 🚫   | 🚫      | ✅   | ✅     | ✅        | 🚫        | ✅       | ✅     | ✅      | ✅       | ✅      | ✅        | ✅    | 🚫    | ⬆️   |
| 引用转发 Reference   | ✅          | 🚫         | 🚫       | 🚫 | 🚫     | 🚫     | 🚫   | 🚫      | 🚫  | ✅     | 🚫       | 🚫        | 🚫      | ✅     | ✅      | 🚫      | ✅      | 🚫       | 🚫   | 🚫    | 🚫   |
| 超级消息 Hyper       | ✅          | 🚫         | 🚫       | ⬇️ | 🚫     | ✅      | 🚫   | 🚫      | ✅   | ✅     | ✅        | 🚫        | 🚫      | ✅     | 🚫     | 🚫      | ✅      | 🚫       | 🚫   | ✅     | 🚫   |
| 按钮 Button        | 🚫         | 🚫         | ⬆️       | 🚫 | 🚫     | ✅      | 🚫   | 🚫      | 🚫  | 🚫    | 🚫       | ⬆️        | ✅       | 🚫    | ✅      | 🚫      | ✅      | 🚫       | 🚫   | 🚫    | 🚫   |
| 其余 Other         | ✅          | ✅          | ✅        | ✅  | ➖      | ✅      | ✅    | ➖       | ✅   | ✅     | ✅        | ➖         | ✅       | ✅     | ✅      | ✅       | ✅      | ✅        | ➖    | ✅     | ➖    |


## 配置项

- ALCONNA_AUTO_SEND_OUTPUT : 是否全局启用输出信息自动发送
- ALCONNA_USE_COMMAND_START : 是否将 COMMAND_START 作为全局命令前缀
- ALCONNA_GLOBAL_COMPLETION: 全局的补全会话配置 (不代表全局启用补全会话)
- ALCONNA_USE_ORIGIN: 是否全局使用原始消息 (即未经过 to_me 等处理的)
- ALCONNA_USE_PARAM: 是否使用特制的 Param 提供更好的依赖注入
- ALCONNA_USE_CMD_SEP: 是否将 COMMAND_SEP 作为全局命令分隔符
- ALCONNA_GLOBAL_EXTENSIONS: 全局加载的扩展, 路径以 . 分隔, 如 foo.bar.baz:DemoExtension
- ALCONNA_CONTEXT_STYLE: 全局命令上下文插值的风格，None 为关闭，bracket 为 {...}，parentheses 为 $(...)
- ALCONNA_ENABLE_SAA_PATCH: 是否启用 SAA 补丁
- ALCONNA_APPLY_FILEHOST: 是否启用文件托管
- ALCONNA_APPLY_FETCH_TARGETS: 是否启动时拉取一次发送对象列表
- ALCONNA_BUILTIN_PLUGINS: 需要加载的alc内置插件集合
- ALCONNA_CONFLICT_RESOLVER: 命令冲突解决策略，default 为保留两个命令，raise 为抛出异常，ignore 为忽略新命令，replace 为替换旧命令
- ALCONNA_RESPONSE_SELF: 是否允许响应自己的消息

## 插件示例

[demo bot](./example/plugins/demo.py)

```python
# echo 插件
from nonebot_plugin_alconna import UniMessage, Command

@Command("echo <...content>").build(auto_send_output=True).handle()
async def _(content: UniMessage):
    await content.finish()
```