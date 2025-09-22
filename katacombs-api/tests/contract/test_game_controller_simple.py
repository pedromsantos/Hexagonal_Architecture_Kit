import pytest
from fastapi.testclient import TestClient

from src.katacombs.infrastructure.adapters.fastapi_app import create_app


class TestGameControllerContract:
    """
    CONTRACT TEST: HTTP Controllers (Driving Adapters)
    Tests API contracts using real implementations (no mocking)
    Focuses on HTTP status codes, request/response format, headers, etc.
    """

    def test_post_game_player_returns_201_with_valid_player_data(self):
        # Arrange - Use real app with real dependencies
        app = create_app()
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

        # Verify location structure
        location = response_data["location"]
        assert "description" in location
        assert "exits" in location
        assert "items" in location

        # Verify bag structure
        bag = response_data["bag"]
        assert "items" in bag

    def test_post_game_player_with_empty_name_returns_400(self):
        # Arrange
        app = create_app()
        client = TestClient(app)

        # Act
        response = client.post(
            "/game/player",
            json={"name": ""},
            headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == 400
        assert "application/json" in response.headers["content-type"]

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
        assert "application/json" in response.headers["content-type"]