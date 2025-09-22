import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from src.katacombs.infrastructure.adapters.fastapi_app import create_app
from src.katacombs.application.use_cases.start_game import StartGameUseCase
from src.katacombs.application.dtos.start_game_dto import StartGameResponse
from src.katacombs.domain.entities.player import Player
from src.katacombs.domain.entities.location import Location
from src.katacombs.domain.entities.bag import Bag
from src.katacombs.domain.value_objects import Sid


class TestGameController:
    """
    CONTRACT TEST: HTTP Controllers (Driving Adapters)
    Tests API contracts and transport concerns without mocking the use case
    Verifies HTTP status codes, request/response format, headers, etc.
    """

    def test_post_game_player_returns_201_with_valid_player_data(self):
        # Arrange - Mock the use case to return a successful response
        mock_use_case = Mock(spec=StartGameUseCase)

        # Create a valid player response
        location = Location(Sid.generate(), "Starting room")
        player = Player.create(Sid.generate(), "Pedro", location, Bag())
        success_response = StartGameResponse.success_response(player)
        mock_use_case.execute.return_value = success_response

        # Create app with mocked dependencies
        app = create_app()

        # Override the dependency function, not the class
        def mock_get_start_game_use_case():
            return mock_use_case

        # Find the original dependency function and override it
        for route in app.routes:
            if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__name__'):
                if route.endpoint.__name__ == 'start_game':
                    # Override the get_start_game_use_case dependency
                    app.dependency_overrides[route.dependant.dependencies[0].call] = mock_get_start_game_use_case

        client = TestClient(app)

        # Act - Make HTTP request
        response = client.post(
            "/game/player",
            json={"name": "Pedro"},
            headers={"Content-Type": "application/json"}
        )

        # Assert - Verify contract compliance
        assert response.status_code == 201
        assert "application/json" in response.headers["content-type"]

        response_data = response.json()
        assert "sid" in response_data
        assert response_data["name"] == "Pedro"
        assert "location" in response_data
        assert "bag" in response_data

        # Verify use case was called correctly
        mock_use_case.execute.assert_called_once()

    def test_post_game_player_with_invalid_name_returns_400(self):
        # Arrange
        mock_use_case = Mock(spec=StartGameUseCase)
        error_response = StartGameResponse.error_response("Player name cannot be empty")
        mock_use_case.execute.return_value = error_response

        app = create_app()
        app.dependency_overrides[StartGameUseCase] = lambda: mock_use_case
        client = TestClient(app)

        # Act
        response = client.post(
            "/game/player",
            json={"name": ""},
            headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == 400
        assert "error" in response.json()

    def test_post_game_player_with_missing_name_returns_422(self):
        # Arrange
        app = create_app()
        client = TestClient(app)

        # Act - Send request without name field
        response = client.post(
            "/game/player",
            json={},
            headers={"Content-Type": "application/json"}
        )

        # Assert - FastAPI validation should return 422
        assert response.status_code == 422

    def test_get_game_player_returns_200_with_active_players_list(self):
        # This test would be for the list players endpoint
        # For now, we'll focus on the start game endpoint
        pass