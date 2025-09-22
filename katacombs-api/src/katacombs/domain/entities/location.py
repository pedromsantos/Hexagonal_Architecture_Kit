from dataclasses import dataclass, field

from ..value_objects import Direction, Sid
from .item import Item


@dataclass
class Location:
    sid: Sid
    description: str
    exits: dict[Direction, Sid | None] = field(default_factory=dict)
    items: list[Item] = field(default_factory=list)

    def __post_init__(self):
        if not self.description.strip():
            raise ValueError("Location description cannot be empty")

    def add_exit(self, direction: Direction, destination_sid: Sid | None = None) -> None:
        self.exits[direction] = destination_sid

    def remove_exit(self, direction: Direction) -> None:
        if direction in self.exits:
            del self.exits[direction]

    def get_exit_destination(self, direction: Direction) -> Sid | None:
        return self.exits.get(direction)

    def can_move(self, direction: Direction) -> bool:
        return direction in self.exits and self.exits[direction] is not None

    def get_available_directions(self) -> list[Direction]:
        return [direction for direction, destination in self.exits.items() if destination is not None]

    def add_item(self, item: Item) -> None:
        if item not in self.items:
            self.items.append(item)

    def remove_item(self, item_sid: Sid) -> Item | None:
        for item in self.items:
            if item.sid == item_sid:
                self.items.remove(item)
                return item
        return None

    def find_item(self, item_sid: Sid) -> Item | None:
        for item in self.items:
            if item.sid == item_sid:
                return item
        return None

    def __eq__(self, other) -> bool:
        if not isinstance(other, Location):
            return False
        return self.sid == other.sid

    def __hash__(self) -> int:
        return hash(self.sid)
