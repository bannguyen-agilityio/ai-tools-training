from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Base for every request body: unknown fields are refused (R29b)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
