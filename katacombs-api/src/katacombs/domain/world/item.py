from dataclasses import dataclass, field

from ..player.sid import Sid
from .action import Action


@dataclass
class Item:
    sid: Sid
    name: str
    description: str
    available_actions: list[Action] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name.strip():
            msg = "Item name cannot be empty"
            raise ValueError(msg)
        if not self.description.strip():
            msg = "Item description cannot be empty"
            raise ValueError(msg)
