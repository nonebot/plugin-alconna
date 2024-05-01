from typing import Literal, Optional

from pydantic import Field, BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    alconna_auto_send_output: bool = False
    """是否全局启用输出信息自动发送"""

    alconna_use_command_start: bool = False
    """是否将 COMMAND_START 作为全局命令前缀"""

    alconna_auto_completion: bool = False
    """是否全局启用命令自动补全"""

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
