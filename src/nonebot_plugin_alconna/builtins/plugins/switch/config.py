from typing import Optional

from pydantic import Field, BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    nbp_alc_switch_enable: str = Field(default="enable")
    nbp_alc_switch_enable_alias: set[str] = Field(default={"启用", "启用指令"})
    nbp_alc_switch_disable: str = Field(default="disable")
    nbp_alc_switch_disable_alias: set[str] = Field(default={"禁用", "禁用指令"})
    nbp_alc_page_size: Optional[int] = Field(ge=2, default=None)
