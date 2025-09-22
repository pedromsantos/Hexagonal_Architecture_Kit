from ...domain.entities.player import Player
from ...domain.repositories.player_repository import PlayerRepository
from ...domain.value_objects import Sid


class InMemoryPlayerRepository(PlayerRepository):
    """Driven Adapter - In-memory implementation of PlayerRepository
    Handles data persistence using in-memory storage for fast testing
    Implements the domain port interface
    """

    def __init__(self) -> None:
        super().__init__()
        self._players: dict[Sid, Player] = {}

    def save(self, player: Player) -> None:
        """Save player to in-memory storage"""
        self._players[player.sid] = player

    def find_by_sid(self, player_sid: Sid) -> Player | None:
        """Find player by SID"""
        return self._players.get(player_sid)

    def find_all_active(self) -> list[Player]:
        """Find all active players"""
        return [player for player in self._players.values() if player.is_active]

    def delete(self, player_sid: Sid) -> bool:
        """Delete player by SID"""
        if player_sid in self._players:
            del self._players[player_sid]
            return True
        return False
