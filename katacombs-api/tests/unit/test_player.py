import pytest

from src.katacombs.domain.entities.bag import Bag
from src.katacombs.domain.entities.location import Location
from src.katacombs.domain.entities.player import Player
from src.katacombs.domain.value_objects import Sid


class TestPlayer:
    """UNIT TEST: Player domain behavior
    Test domain logic for Player aggregate
    """

    def test_player_can_be_created_with_valid_data(self):
        # Arrange
        player_sid = Sid.generate()
        name = "Pedro"
        location = Location(sid=Sid.generate(), description="Starting room")
        bag = Bag()

        # Act
        player = Player.create(player_sid, name, location, bag)

        # Assert
        assert player.sid == player_sid
        assert player.name == name
        assert player.location == location
        assert player.bag == bag
        assert player.is_active is True

    def test_player_name_cannot_be_empty(self):
        # Arrange
        player_sid = Sid.generate()
        location = Location(Sid.generate(), "Starting room")
        bag = Bag()

        # Act & Assert
        with pytest.raises(ValueError, match="Player name cannot be empty"):
            Player.create(player_sid, "", location, bag)

    def test_player_can_move_to_new_location(self):
        # Arrange
        player_sid = Sid.generate()
        original_location = Location(Sid.generate(), "Original room")
        new_location = Location(Sid.generate(), "New room")
        player = Player.create(player_sid, "Pedro", original_location, Bag())

        # Act
        player.move_to_location(new_location)

        # Assert
        assert player.location == new_location

    def test_player_can_quit_game(self):
        # Arrange
        player = Player.create(Sid.generate(), "Pedro", Location(Sid.generate(), "Room"), Bag())

        # Act
        player.quit_game()

        # Assert
        assert player.is_active is False
