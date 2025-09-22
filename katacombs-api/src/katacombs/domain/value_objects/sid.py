import re
import secrets
import uuid
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Sid:
    value: str

    PATTERN: ClassVar[str] = r"^[0-9]{6}-[0-9]{12}-[0-9]{8}$"

    def __post_init__(self) -> None:
        if not self._is_valid(self.value):
            msg = f"Invalid Sid format: {self.value}"
            raise ValueError(msg)

    @classmethod
    def _is_valid(cls, value: str) -> bool:
        return bool(re.match(cls.PATTERN, value))

    @classmethod
    def generate(cls) -> "Sid":
        """Generate a new Sid using UUID4 and formatting it to match the pattern"""
        uuid_str = str(uuid.uuid4()).replace("-", "")
        # Format: XXXXXX-XXXXXXXXXXXX-XXXXXXXX (6-12-8 digits)
        formatted = f"{uuid_str[:6]}-{uuid_str[6:18]}-{uuid_str[18:26]}"
        # Ensure all characters are digits by replacing hex chars with digits
        formatted = "".join(
            c if c.isdigit() else str(ord(c) % 10) for c in formatted if c.isalnum() or c == "-"
        )
        # Reconstruct with proper format
        parts = formatted.split("-")
        min_parts = 3
        if len(parts) >= min_parts:
            sid_value = f"{parts[0][:6].zfill(6)}-{parts[1][:12].zfill(12)}-{parts[2][:8].zfill(8)}"
        else:
            # Fallback: generate from scratch using secure random
            part1 = secrets.randbelow(900_000) + 100_000
            part2 = secrets.randbelow(900_000_000_000) + 100_000_000_000
            part3 = secrets.randbelow(90_000_000) + 10_000_000
            sid_value = f"{part1}-{part2}-{part3}"

        return cls(sid_value)

    def __str__(self) -> str:
        return self.value
