"""Represent source fields without collapsing absent, empty, or populated values."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SourceFieldState(StrEnum):
    MISSING = "missing"
    EMPTY = "empty"
    VALUE = "value"


@dataclass(frozen=True, slots=True)
class SourceField:
    """A raw source element's text and attributes, preserved as strings."""

    state: SourceFieldState
    value: str | None = None
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.state, SourceFieldState):
            raise TypeError("Source field state must be a SourceFieldState.")

        if self.state is SourceFieldState.MISSING:
            if self.value is not None or self.attributes:
                raise ValueError("Missing source fields cannot have a value or attributes.")
        elif self.state is SourceFieldState.EMPTY:
            if self.value != "":
                raise ValueError("Empty source fields must have an empty-string value.")
        elif self.state is SourceFieldState.VALUE and (self.value is None or self.value == ""):
            raise ValueError("Value source fields must have a non-empty string value.")

        if not isinstance(self.attributes, tuple) or any(
            not isinstance(attribute, tuple)
            or len(attribute) != 2
            or not all(isinstance(part, str) for part in attribute)
            for attribute in self.attributes
        ):
            raise TypeError("Source attributes must be a tuple of string name/value pairs.")

    @classmethod
    def missing(cls) -> SourceField:
        return cls(state=SourceFieldState.MISSING)

    @classmethod
    def empty(cls, *, attributes: tuple[tuple[str, str], ...] = ()) -> SourceField:
        return cls(state=SourceFieldState.EMPTY, value="", attributes=attributes)

    @classmethod
    def of(cls, value: str, *, attributes: tuple[tuple[str, str], ...] = ()) -> SourceField:
        if value == "":
            return cls.empty(attributes=attributes)
        return cls(state=SourceFieldState.VALUE, value=value, attributes=attributes)
