import pytest
from pydantic import ValidationError

from app.core.schemas import StrictModel


class Body(StrictModel):
    name: str


def test_unknown_fields_are_refused() -> None:
    with pytest.raises(ValidationError):
        Body.model_validate({"name": "a", "extra": 1})


def test_strings_are_stripped() -> None:
    assert Body(name="  a  ").name == "a"
