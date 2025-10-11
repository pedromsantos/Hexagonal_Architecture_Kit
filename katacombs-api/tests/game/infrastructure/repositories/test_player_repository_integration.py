from src.game.domain.player import Bag, Player, Sid
from src.game.infrastructure.repositories.in_memory_player_repository import (
    InMemoryPlayerRepository,
)
from src.game.infrastructure.sid_generator import SidGenerator


class TestPlayerRepository:
    """INTEGRATION TEST: Player Repository Implementation (WRITE-SIDE)
    Tests the driven adapter implementation with real storage
    Uses in-memory implementation for fast testing

    IMPORTANT: This tests the WRITE-SIDE repository only.
    For query operations, see tests for PlayerProjectionRepository.
    """

    def test_save_and_find_player_by_sid(self):
        # Arrange
        repo = InMemoryPlayerRepository()
        player_sid = SidGenerator.generate()
        location_sid = SidGenerator.generate()
        player = Player.create(player_sid, "Pedro", location_sid, Bag())

        # Act - Save player
        repo.save(player)
        retrieved_player = repo.find_by_sid(player_sid)

        # Assert - Verify data persistence and retrieval
        assert retrieved_player is not None
        assert retrieved_player.sid == player.sid
        assert retrieved_player.name == player.name
        assert retrieved_player.is_active == player.is_active

    def test_delete_player(self):
        # Arrange
        repo = InMemoryPlayerRepository()
        player_sid = SidGenerator.generate()
        location_sid = SidGenerator.generate()
        player = Player.create(player_sid, "Pedro", location_sid, Bag())

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
        nonexistent_sid = SidGenerator.generate()

        # Act
        result = repo.find_by_sid(nonexistent_sid)

        # Assert
        assert result is None
