"""In-memory implementation of PlayerProjectionRepository for read operations"""

from ...application.queries.player_projection_repository import (
    PlayerDetailsDto,
    PlayerListItemDto,
    PlayerProjectionRepository,
)
from ...domain.player import Player, Sid
from ...domain.world import World


class InMemoryPlayerProjectionRepository(PlayerProjectionRepository):
    """In-memory projection repository for player queries

    This implementation reads from the same data source as the write-side
    repository but returns DTOs directly without loading full domain objects.

    In a production system, this could:
    - Read from a denormalized view/table
    - Use a separate read database
    - Cache frequently accessed data
    """

    def __init__(self, players: dict[Sid, Player], world: World):
        """Initialize with access to player data and world

        Args:
            players: Dictionary of players (shared with write repository)
            world: World aggregate for location lookups
        """
        self._players = players
        self._world = world

    def find_all_active_players(self) -> list[PlayerListItemDto]:
        """Get list of all active players with denormalized location data"""
        result = []

        for player in self._players.values():
            if player.is_active:
                # Fetch location description from World (denormalized for read)
                location = self._world.get_location(player.location_sid)
                location_description = location.description if location else "Unknown location"

                result.append(
                    PlayerListItemDto(
                        sid=str(player.sid.value),
                        name=player.name,
                        location_description=location_description,
                        is_active=player.is_active,
                    )
                )

        return result

    def get_player_details(self, player_sid: str) -> PlayerDetailsDto | None:
        """Get detailed player information for display"""
        # Find player by SID
        player = self._players.get(Sid(player_sid))
        if not player:
            return None

        # Fetch location description from World
        location = self._world.get_location(player.location_sid)
        location_description = location.description if location else "Unknown location"

        return PlayerDetailsDto(
            sid=str(player.sid.value),
            name=player.name,
            location_sid=str(player.location_sid.value),
            location_description=location_description,
            bag_item_count=player.bag.item_count(),
            is_active=player.is_active,
        )
