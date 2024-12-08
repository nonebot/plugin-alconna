from typing import Literal, Optional

from pydantic import Field, BaseModel

from .model import CompConfig


class Config(BaseModel):
    """Plugin Config Here"""

    alconna_auto_send_output: Optional[bool] = None
    """是否全局启用输出信息自动发送"""

    alconna_use_command_start: bool = False
    """是否将 COMMAND_START 作为全局命令前缀"""

    alconna_global_completion: Optional[CompConfig] = Field(None, strict=True)
    """全局的补全会话配置 (不代表全局启用补全会话)"""

    alconna_use_origin: bool = False
    """是否全局使用原始消息 (即未经过 to_me 等处理的)"""

    alconna_use_command_sep: bool = False
    """是否将 COMMAND_SEP 作为全局命令分隔符"""

    alconna_global_extensions: list[str] = Field(default_factory=list)
    """全局加载的扩展, 路径以 . 分隔, 如 foo.bar.baz:DemoExtension"""

    alconna_context_style: Optional[Literal["bracket", "parentheses"]] = Field(default=None)
    """全局命令上下文插值的风格，None 为关闭，bracket 为 {...}，parentheses 为 $(...)"""

    alconna_enable_saa_patch: bool = False
    """是否启用 SAA 补丁"""

    alconna_apply_filehost: bool = False
    """是否启用文件托管"""

    alconna_apply_fetch_targets: bool = False
    """是否启动时拉取一次发送对象列表"""

    alconna_builtin_plugins: set[str] = Field(default_factory=set)
    """需要加载的alc内置插件集合"""

    alconna_conflict_resolver: Literal["raise", "default", "ignore", "replace"] = Field(default="default")
    """命令冲突解决策略，default 为保留两个命令，raise 为抛出异常，ignore 为忽略新命令，replace 为替换旧命令"""

    alconna_response_self: bool = False
    """是否响应自身发送的消息"""
