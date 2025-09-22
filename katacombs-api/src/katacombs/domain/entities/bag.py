from dataclasses import dataclass, field

from ..value_objects import Sid
from .item import Item


@dataclass
class Bag:
    items: list[Item] = field(default_factory=list)
    max_capacity: int = 10

    def add_item(self, item: Item) -> None:
        if self.is_full():
            raise ValueError("Bag is full, cannot add more items")
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

    def has_item(self, item_sid: Sid) -> bool:
        return self.find_item(item_sid) is not None

    def is_full(self) -> bool:
        return len(self.items) >= self.max_capacity

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def get_item_count(self) -> int:
        return len(self.items)
