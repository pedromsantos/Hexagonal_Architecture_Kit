import pytest
from fastapi.testclient import TestClient

from src.katacombs.infrastructure.adapters.fastapi_app import create_app


class TestStartGameE2E:
    """
    END-TO-END TEST: Complete user journey through real transport and infrastructure
    Uses real HTTP server and real (in-memory) storage
    Tests the complete system behavior from HTTP request to final response
    """

    def test_complete_user_registration_journey_e2e(self):
        # Arrange - Real HTTP server with real dependencies
        app = create_app()
        client = TestClient(app)

        # Act - Real HTTP call to real server (external system provides SID)
        response = client.post(
            "/game/player",
            json={"name": "Pedro", "sid": "123456-123456789012-12345678"},
            headers={"Content-Type": "application/json"}
        )

        # Assert - Verify complete system behavior
        assert response.status_code == 201

        response_data = response.json()
        player_sid = response_data["sid"]

        # Verify player was created correctly
        assert response_data["name"] == "Pedro"
        assert len(player_sid) > 0

        # Verify location data structure
        location = response_data["location"]
        assert "description" in location
        assert "Katacombs" in location["description"]  # Should contain starting location text
        assert isinstance(location["exits"], list)
        assert len(location["exits"]) > 0  # Should have some exits

        # Verify starting items are available
        assert isinstance(location["items"], list)
        # Should have at least a torch in the starting location
        item_names = [item["name"] for item in location["items"]]
        assert "Torch" in item_names

        # Verify empty bag
        bag = response_data["bag"]
        assert isinstance(bag["items"], list)
        assert len(bag["items"]) == 0  # Should start with empty bag

    def test_multiple_players_can_start_games_independently_e2e(self):
        # Arrange - Real application
        app = create_app()
        client = TestClient(app)

        # Act - Create two different players (each with unique SID from external system)
        response1 = client.post("/game/player", json={"name": "Alice", "sid": "111111-111111111111-11111111"})
        response2 = client.post("/game/player", json={"name": "Bob", "sid": "222222-222222222222-22222222"})

        # Assert - Both players created successfully with different SIDs
        assert response1.status_code == 201
        assert response2.status_code == 201

        player1_data = response1.json()
        player2_data = response2.json()

        # Verify they have different identities
        assert player1_data["sid"] != player2_data["sid"]
        assert player1_data["name"] == "Alice"
        assert player2_data["name"] == "Bob"

        # Both should start in the same location (same description)
        assert player1_data["location"]["description"] == player2_data["location"]["description"]

    def test_error_handling_works_end_to_end(self):
        # Arrange
        app = create_app()
        client = TestClient(app)

        # Act - Try to create player with invalid data
        response = client.post(
            "/game/player",
            json={"name": "", "sid": "123456-123456789012-12345678"},
            headers={"Content-Type": "application/json"}
        )

        # Assert - Error handled properly through entire stack
        assert response.status_code == 400
        assert "error" in response.json() or "detail" in response.json()