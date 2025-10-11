"""Read-side repository interface for player queries (CQRS)"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PlayerListItemDto:
    """DTO for player list item - shaped for UI display

    This DTO is optimized for read operations and may include
    denormalized data from multiple aggregates.
    """

    sid: str
    name: str
    location_description: str
    is_active: bool


@dataclass
class PlayerDetailsDto:
    """DTO for detailed player information"""

    sid: str
    name: str
    location_sid: str
    location_description: str
    bag_item_count: int
    is_active: bool


class PlayerProjectionRepository(ABC):
    """Read-side repository for player queries

    This repository bypasses the domain layer and returns DTOs directly.
    It's optimized for read performance and can use denormalized data,
    views, or separate read databases.

    IMPORTANT: Use this ONLY for queries (read operations).
    For commands (write operations), use PlayerRepository.
    """

    @abstractmethod
    def find_all_active_players(self) -> list[PlayerListItemDto]:
        """Get list of all active players with denormalized location data"""

    @abstractmethod
    def get_player_details(self, player_sid: str) -> PlayerDetailsDto | None:
        """Get detailed player information for display"""
