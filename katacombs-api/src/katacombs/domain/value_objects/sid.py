from dataclasses import dataclass
import re
import uuid
from typing import ClassVar


@dataclass(frozen=True)
class Sid:
    value: str

    PATTERN: ClassVar[str] = r"^[0-9]{6}-[0-9]{12}-[0-9]{8}$"

    def __post_init__(self):
        if not self._is_valid(self.value):
            raise ValueError(f"Invalid Sid format: {self.value}")

    @classmethod
    def _is_valid(cls, value: str) -> bool:
        return bool(re.match(cls.PATTERN, value))

    @classmethod
    def generate(cls) -> "Sid":
        """Generate a new Sid using UUID4 and formatting it to match the pattern"""
        uuid_str = str(uuid.uuid4()).replace('-', '')
        # Format: XXXXXX-XXXXXXXXXXXX-XXXXXXXX (6-12-8 digits)
        formatted = f"{uuid_str[:6]}-{uuid_str[6:18]}-{uuid_str[18:26]}"
        # Ensure all characters are digits by replacing hex chars with digits
        formatted = ''.join(c if c.isdigit() else str(ord(c) % 10) for c in formatted if c.isalnum() or c == '-')
        # Reconstruct with proper format
        parts = formatted.split('-')
        if len(parts) >= 3:
            sid_value = f"{parts[0][:6].zfill(6)}-{parts[1][:12].zfill(12)}-{parts[2][:8].zfill(8)}"
        else:
            # Fallback: generate from scratch
            import random
            sid_value = f"{random.randint(100000, 999999)}-{random.randint(100000000000, 999999999999)}-{random.randint(10000000, 99999999)}"

        return cls(sid_value)

    def __str__(self) -> str:
        return self.value