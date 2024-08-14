from typing import Optional

from pydantic import Field, BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    nbp_alc_help_text: str = Field(default="help")
    nbp_alc_help_alias: set[str] = Field(default={"帮助", "命令帮助"})
    nbp_alc_help_all_alias: set[str] = Field(default={"所有帮助", "所有命令帮助"})
    nbp_alc_page_size: Optional[int] = Field(ge=2, default=None)
