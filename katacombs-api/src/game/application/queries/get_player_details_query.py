"""Query handler for getting detailed player information"""

from dataclasses import dataclass

from .player_projection_repository import PlayerDetailsDto, PlayerProjectionRepository


@dataclass
class GetPlayerDetailsQuery:
    """Query to get detailed information about a specific player

    Args:
        player_sid: The unique identifier of the player
    """

    player_sid: str


class GetPlayerDetailsQueryHandler:
    """Query handler for getting detailed player information

    This handler uses the read-side projection repository to fetch
    denormalized player data optimized for detailed display.
    """

    def __init__(self, player_projection_repository: PlayerProjectionRepository):
        self._player_projection_repository = player_projection_repository

    def handle(self, query: GetPlayerDetailsQuery) -> PlayerDetailsDto | None:
        """Execute the query and return player details

        Args:
            query: The query object containing the player SID

        Returns:
            PlayerDetailsDto if player exists, None otherwise
        """
        return self._player_projection_repository.get_player_details(query.player_sid)
