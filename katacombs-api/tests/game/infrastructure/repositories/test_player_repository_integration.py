from src.game.domain.player import Bag, Player, Sid
from src.game.domain.world import Location
from src.game.infrastructure.repositories.in_memory_player_repository import (
    InMemoryPlayerRepository,
)


class TestPlayerRepository:
    """INTEGRATION TEST: Player Repository Implementation
    Tests the driven adapter implementation with real storage
    Uses in-memory implementation for fast testing
    """

    def test_save_and_find_player_by_sid(self):
        # Arrange
        repo = InMemoryPlayerRepository()
        player_sid = Sid.generate()
        location = Location(Sid.generate(), "Test room")
        player = Player.create(player_sid, "Pedro", location, Bag())

        # Act - Save player
        repo.save(player)
        retrieved_player = repo.find_by_sid(player_sid)

        # Assert - Verify data persistence and retrieval
        assert retrieved_player is not None
        assert retrieved_player.sid == player.sid
        assert retrieved_player.name == player.name
        assert retrieved_player.is_active == player.is_active

    def test_find_all_active_players(self):
        # Arrange
        repo = InMemoryPlayerRepository()
        location = Location(Sid.generate(), "Test room")

        active_player = Player.create(Sid.generate(), "Active", location, Bag())
        inactive_player = Player.create(Sid.generate(), "Inactive", location, Bag())
        inactive_player.quit_game()

        # Act
        repo.save(active_player)
        repo.save(inactive_player)
        active_players = repo.find_all_active()

        # Assert
        assert len(active_players) == 1
        assert active_players[0].sid == active_player.sid

    def test_delete_player(self):
        # Arrange
        repo = InMemoryPlayerRepository()
        player_sid = Sid.generate()
        location = Location(Sid.generate(), "Test room")
        player = Player.create(player_sid, "Pedro", location, Bag())

        repo.save(player)

        # Act
        result = repo.delete(player_sid)
        retrieved_player = repo.find_by_sid(player_sid)

        # Assert
        assert result is True
        assert retrieved_player is None

    def test_find_nonexistent_player_returns_none(self):
        # Arrange
        repo = InMemoryPlayerRepository()
        nonexistent_sid = Sid.generate()

        # Act
        result = repo.find_by_sid(nonexistent_sid)

        # Assert
        assert result is None
