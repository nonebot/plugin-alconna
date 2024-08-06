from pydantic import Field, BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    nbp_alc_with_text: str = Field(default="with")
    nbp_alc_with_alias: set[str] = Field(default={"局部前缀"})
