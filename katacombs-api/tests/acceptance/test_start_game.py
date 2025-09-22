import pytest
from unittest.mock import Mock

from src.katacombs.application.use_cases.start_game import StartGameUseCase
from src.katacombs.domain.repositories.player_repository import PlayerRepository
from src.katacombs.domain.repositories.location_repository import LocationRepository
from src.katacombs.application.dtos.start_game_dto import StartGameCommand, StartGameResponse


class TestStartGame:
    """
    ACCEPTANCE TEST: User Story - "As a player, I want to start a new game so that I can begin playing Katacombs"

    This test defines our DEFINITION OF DONE for the start game behavior.
    It should FAIL (RED) until the complete behavior is implemented.
    """

    def test_player_can_start_new_game(self):
        # Arrange - Mock infrastructure dependencies (driven ports)
        mock_player_repo = Mock(spec=PlayerRepository)
        mock_location_repo = Mock(spec=LocationRepository)

        # Create the use case (this interface doesn't exist yet)
        use_case = StartGameUseCase(mock_player_repo, mock_location_repo)

        # Act - Execute the behavior we want to implement
        command = StartGameCommand(player_name="Pedro")
        result = use_case.execute(command)

        # Assert - Verify the complete behavior
        assert isinstance(result, StartGameResponse)
        assert result.success is True
        assert result.player.name == "Pedro"
        assert result.player.sid is not None
        assert result.player.location is not None
        assert result.player.bag is not None

        # Verify infrastructure interactions
        mock_player_repo.save.assert_called_once()
        mock_location_repo.find_starting_location.assert_called_once()


# This test should be RED (failing) - that's our Definition of Done for the behavior being implemented
# We DON'T try to make this pass immediately - we use it as our north star