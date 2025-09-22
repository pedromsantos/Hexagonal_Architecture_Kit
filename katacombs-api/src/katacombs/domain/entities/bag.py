from dataclasses import dataclass, field

from .item import Item


@dataclass
class Bag:
    items: list[Item] = field(default_factory=list)
