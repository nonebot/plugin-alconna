from typing import List

from pydantic import Extra, Field, BaseModel


class Config(BaseModel, extra=Extra.ignore):
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

    alconna_global_extensions: List[str] = Field(default_factory=list)
    """全局加载的扩展, 路径以 . 分隔, 如 foo.bar.baz:DemoExtension"""
