"""Query handler for getting all active players"""

from dataclasses import dataclass

from .player_projection_repository import PlayerListItemDto, PlayerProjectionRepository


@dataclass
class GetAllActivePlayersQuery:
    """Query to get all active players

    This is a pure query with no parameters - it returns all currently active players.
    Following CQRS, this query does not modify any state.
    """

    pass


class GetAllActivePlayersQueryHandler:
    """Query handler for getting all active players

    This handler uses the read-side projection repository to fetch
    denormalized player data optimized for display.
    """

    def __init__(self, player_projection_repository: PlayerProjectionRepository):
        self._player_projection_repository = player_projection_repository

    def handle(self, query: GetAllActivePlayersQuery) -> list[PlayerListItemDto]:
        """Execute the query and return active players

        Args:
            query: The query object (contains no parameters for this query)

        Returns:
            List of PlayerListItemDto objects representing active players
        """
        return self._player_projection_repository.find_all_active_players()
