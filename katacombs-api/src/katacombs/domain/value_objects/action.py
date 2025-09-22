from enum import Enum


class Action(Enum):
    OPEN = "open"
    CLOSE = "close"
    PICK = "pick"
    DROP = "drop"
    USE = "use"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, action: str) -> "Action":
        for a in cls:
            if a.value == action.lower():
                return a
        msg = f"Invalid action: {action}"
        raise ValueError(msg)
