from pydantic import Extra, BaseModel


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    alconna_auto_send_output: bool = False
    """是否全局启用输出信息自动发送"""

    alconna_use_command_start: bool = False
    """是否将 COMMAND_START 作为全局命令前缀"""

    alconna_auto_completion: bool = False
    """是否全局启用命令自动补全"""
