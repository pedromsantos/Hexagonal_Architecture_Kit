from enum import Enum


class Action(Enum):
    PICK = "pick"
    USE = "use"

    def __str__(self) -> str:
        return self.value
