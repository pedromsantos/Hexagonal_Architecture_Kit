from abc import ABC, abstractmethod

from .player import Player
from .sid import Sid


class PlayerRepository(ABC):
    """Driven Port - Repository interface for Player aggregate
    This belongs in the domain layer as it represents a domain concept
    """

    @abstractmethod
    def save(self, player: Player) -> None:
        pass

    @abstractmethod
    def find_by_sid(self, player_sid: Sid) -> Player | None:
        pass

    @abstractmethod
    def find_all_active(self) -> list[Player]:
        pass

    @abstractmethod
    def delete(self, player_sid: Sid) -> bool:
        pass
