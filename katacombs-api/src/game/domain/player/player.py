from dataclasses import dataclass

from .bag import Bag
from .sid import Sid


@dataclass
class Player:
    """Player Aggregate Root
    Represents a player in the Katacombs game
    """

    sid: Sid
    name: str
    location_sid: Sid
    bag: Bag
    is_active: bool = True

    @classmethod
    def create(cls, sid: Sid, name: str, location_sid: Sid, bag: Bag) -> "Player":
        """Factory method for creating a new Player"""
        if not name.strip():
            msg = "Player name cannot be empty"
            raise ValueError(msg)

        return cls(sid=sid, name=name.strip(), location_sid=location_sid, bag=bag, is_active=True)

    def move_to_location(self, new_location_sid: Sid) -> None:
        """Move player to a new location"""
        self.location_sid = new_location_sid

    def quit_game(self) -> None:
        """Mark player as inactive (quit the game)"""
        self.is_active = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Player):
            return False
        return self.sid == other.sid

    def __hash__(self) -> int:
        return hash(self.sid)
