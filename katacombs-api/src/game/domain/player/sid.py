import re
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Sid:
    """Session ID value object

    A domain value object representing a unique session identifier.

    IMPORTANT: This class does NOT generate IDs. SIDs must be provided by
    external systems (UI, API client, infrastructure layer).
    Use SidGenerator from infrastructure layer for ID generation.
    """

    value: str

    PATTERN: ClassVar[str] = r"^[0-9]{6}-[0-9]{12}-[0-9]{8}$"

    def __post_init__(self) -> None:
        if not self._is_valid(self.value):
            msg = f"Invalid Sid format: {self.value}"
            raise ValueError(msg)

    @classmethod
    def _is_valid(cls, value: str) -> bool:
        return bool(re.match(cls.PATTERN, value))

    def __str__(self) -> str:
        return self.value
