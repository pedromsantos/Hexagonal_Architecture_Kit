from abc import ABC, abstractmethod

from .player import Player
from .sid import Sid


class PlayerRepository(ABC):
    """Driven Port - Write-side repository interface for Player aggregate

    This belongs in the domain layer as it represents a domain concept.

    IMPORTANT: This is a WRITE-SIDE repository for command operations only.
    For read operations (queries), use PlayerProjectionRepository instead.
    """

    @abstractmethod
    def save(self, player: Player) -> None:
        """Persist player changes after command execution"""
        pass

    @abstractmethod
    def find_by_sid(self, player_sid: Sid) -> Player | None:
        """Load player aggregate for COMMAND operations only.

        Use this ONLY when you need to execute domain behavior.
        For read-only queries, use PlayerProjectionRepository.
        """
        pass

    @abstractmethod
    def delete(self, player_sid: Sid) -> bool:
        """Remove player from persistence"""
        pass
