from dataclasses import dataclass, field

from ..value_objects import Direction, Sid
from .item import Item


@dataclass
class Location:
    sid: Sid
    description: str
    exits: dict[Direction, Sid | None] = field(default_factory=dict)
    items: list[Item] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.description.strip():
            msg = "Location description cannot be empty"
            raise ValueError(msg)

    def add_exit(self, direction: Direction, destination_sid: Sid | None = None) -> None:
        self.exits[direction] = destination_sid

    def get_available_directions(self) -> list[Direction]:
        return [
            direction for direction, destination in self.exits.items() if destination is not None
        ]

    def add_item(self, item: Item) -> None:
        self.items.append(item)
