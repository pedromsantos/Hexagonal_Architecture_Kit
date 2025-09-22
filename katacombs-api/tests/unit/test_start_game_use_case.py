import pytest
from unittest.mock import Mock

from src.katacombs.application.use_cases.start_game import StartGameUseCase
from src.katacombs.domain.repositories.player_repository import PlayerRepository
from src.katacombs.domain.repositories.location_repository import LocationRepository
from src.katacombs.application.dtos.start_game_dto import StartGameCommand, StartGameResponse


class TestStartGameUseCase:
    """
    UNIT TEST: Use Case orchestration logic
    This test should fail until we implement the use case orchestration
    """

    def test_use_case_orchestrates_player_creation_and_starting_location(self):
        # Arrange - Mock driven ports
        mock_player_repo = Mock(spec=PlayerRepository)
        mock_location_repo = Mock(spec=LocationRepository)

        # Mock the starting location
        mock_starting_location = Mock()
        mock_location_repo.find_starting_location.return_value = mock_starting_location

        use_case = StartGameUseCase(mock_player_repo, mock_location_repo)
        command = StartGameCommand(player_name="Pedro")

        # Act
        result = use_case.execute(command)

        # Assert - Verify orchestration logic only (no business logic)
        assert isinstance(result, StartGameResponse)
        assert result.success is True

        # Verify the use case called the right repositories
        mock_location_repo.find_starting_location.assert_called_once()
        mock_player_repo.save.assert_called_once()


# This unit test should be RED - we'll make it GREEN by implementing the use case