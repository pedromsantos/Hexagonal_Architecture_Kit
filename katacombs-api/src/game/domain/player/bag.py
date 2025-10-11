from dataclasses import dataclass, field

from .sid import Sid


@dataclass
class Bag:
    """Bag value object for holding player's items"""

    item_sids: list[Sid] = field(default_factory=list)

    def add_item(self, item_sid: Sid) -> None:
        """Add item to bag by its SID"""
        self.item_sids.append(item_sid)

    def remove_item(self, item_sid: Sid) -> bool:
        """Remove item from bag by its SID, return success"""
        try:
            self.item_sids.remove(item_sid)
            return True
        except ValueError:
            return False

    def has_item(self, item_sid: Sid) -> bool:
        """Check if bag contains item"""
        return item_sid in self.item_sids

    def is_empty(self) -> bool:
        """Check if bag is empty"""
        return len(self.item_sids) == 0

    def item_count(self) -> int:
        """Get number of items in bag"""
        return len(self.item_sids)
