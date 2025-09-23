from unittest.mock import Mock

from src.game.application.dtos.start_game_dto import StartGameCommand, StartGameResponse
from src.game.application.use_cases.start_game import StartGameUseCase
from src.game.domain.player import PlayerRepository, Sid
from src.game.domain.world import Location, WorldRepository


class TestStartGameUseCase:
    """UNIT TEST: Use Case orchestration logic
    This test should fail until we implement the use case orchestration
    """

    def test_use_case_orchestrates_player_creation_and_starting_location(self):
        # Arrange - Mock ONLY the driven ports (adapters), NOT domain entities
        mock_player_repo = Mock(spec=PlayerRepository)
        mock_world_repo = Mock(spec=WorldRepository)

        # Use REAL domain entities - never mock domain objects
        from src.game.domain.world import World
        real_starting_location = Location(
            sid=Sid.generate(), description="Starting location for the game"
        )
        # Create a real World aggregate with the test location
        real_world = World(
            locations={real_starting_location.sid: real_starting_location},
            starting_location_sid=real_starting_location.sid
        )
        mock_world_repo.get_world.return_value = real_world

        use_case = StartGameUseCase(mock_player_repo, mock_world_repo)
        command = StartGameCommand(player_name="Pedro", player_sid="123456-123456789012-12345678")

        # Act
        result = use_case.execute(command)

        # Assert - Verify orchestration logic only (no business logic)
        assert isinstance(result, StartGameResponse)
        assert result.success is True

        # Verify the use case called the right repositories (adapters)
        # Only verify COMMANDS (side effects), not QUERIES (data retrieval)
        mock_player_repo.save.assert_called_once()  # ✅ Command - causes state change
        # Do NOT verify: mock_world_repo.find_starting_location.assert_called_once()  # ❌ Query - implementation detail


# This unit test should be RED - we'll make it GREEN by implementing the use case
