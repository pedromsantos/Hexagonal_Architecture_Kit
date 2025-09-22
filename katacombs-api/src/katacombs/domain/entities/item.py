from dataclasses import dataclass, field
from typing import List

from ..value_objects import Sid, Action


@dataclass
class Item:
    sid: Sid
    name: str
    description: str
    available_actions: List[Action] = field(default_factory=list)

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Item name cannot be empty")
        if not self.description.strip():
            raise ValueError("Item description cannot be empty")

    def can_perform_action(self, action: Action) -> bool:
        return action in self.available_actions

    def add_action(self, action: Action) -> None:
        if action not in self.available_actions:
            self.available_actions.append(action)

    def remove_action(self, action: Action) -> None:
        if action in self.available_actions:
            self.available_actions.remove(action)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Item):
            return False
        return self.sid == other.sid

    def __hash__(self) -> int:
        return hash(self.sid)