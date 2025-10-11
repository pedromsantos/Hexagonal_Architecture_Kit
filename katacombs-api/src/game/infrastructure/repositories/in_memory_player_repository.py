from ...domain.player import Player, PlayerRepository, Sid


class InMemoryPlayerRepository(PlayerRepository):
    """Driven Adapter - In-memory implementation of PlayerRepository (WRITE-SIDE)

    Handles data persistence using in-memory storage for fast testing.
    Implements the domain port interface for command operations.

    IMPORTANT: This is the WRITE-SIDE repository.
    For queries, use InMemoryPlayerProjectionRepository instead.
    """

    def __init__(self) -> None:
        super().__init__()
        self._players: dict[Sid, Player] = {}

    def save(self, player: Player) -> None:
        """Save player to in-memory storage"""
        self._players[player.sid] = player

    def find_by_sid(self, player_sid: Sid) -> Player | None:
        """Find player by SID for command operations"""
        return self._players.get(player_sid)

    def delete(self, player_sid: Sid) -> bool:
        """Delete player by SID"""
        if player_sid in self._players:
            del self._players[player_sid]
            return True
        return False

    def get_players_dict(self) -> dict[Sid, Player]:
        """Get internal players dictionary for projection repository

        This is a temporary helper method to allow the projection repository
        to access the same data. In a real system, they might use separate
        databases or the projection repo would be updated via events.
        """
        return self._players
