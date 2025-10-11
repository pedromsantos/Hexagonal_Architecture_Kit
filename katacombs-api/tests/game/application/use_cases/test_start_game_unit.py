from unittest.mock import Mock

from src.game.application.commands import (
    StartGameCommand,
    StartGameCommandHandler,
    StartGameResponse,
)
from src.game.domain.player import PlayerRepository, Sid
from src.game.domain.world import Location, WorldRepository
from src.game.infrastructure.sid_generator import SidGenerator


class TestStartGameCommandHandler:
    """UNIT TEST: Use Case orchestration logic
    This test should fail until we implement the use case orchestration
    """

    def test_command_handler_orchestrates_player_creation_and_starting_location(self):
        # Arrange - Mock ONLY the driven ports (adapters), NOT domain entities
        mock_player_repo = Mock(spec=PlayerRepository)
        mock_world_repo = Mock(spec=WorldRepository)

        # Use REAL domain entities - never mock domain objects
        from src.game.domain.world import World
        real_starting_location = Location(
            sid=SidGenerator.generate(), description="Starting location for the game"
        )
        # Create a real World aggregate with the test location
        real_world = World(
            locations={real_starting_location.sid: real_starting_location},
            starting_location_sid=real_starting_location.sid
        )
        mock_world_repo.get_world.return_value = real_world

        command_handler = StartGameCommandHandler(mock_player_repo, mock_world_repo)
        command = StartGameCommand(player_name="Pedro", player_sid="123456-123456789012-12345678")

        # Act
        result = command_handler.execute(command)

        # Assert - Verify orchestration logic only (no business logic)
        assert isinstance(result, StartGameResponse)
        assert result.success is True

        # Verify the command handler called the right repositories (adapters)
        # Only verify COMMANDS (side effects), not QUERIES (data retrieval)
        mock_player_repo.save.assert_called_once()  # ✅ Command - causes state change
        # Do NOT verify: mock_world_repo.find_starting_location.assert_called_once()  # ❌ Query - implementation detail


# This unit test verifies command handler orchestration logic
