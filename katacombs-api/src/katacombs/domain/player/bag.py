from dataclasses import dataclass, field

from ..world.item import Item


@dataclass
class Bag:
    items: list[Item] = field(default_factory=list)
