import pytest

from src.game.domain.player import Bag, Player, Sid
from src.game.infrastructure.sid_generator import SidGenerator


class TestPlayer:
    """UNIT TEST: Player domain behavior
    Test domain logic for Player aggregate
    """

    def test_player_can_be_created_with_valid_data(self):
        player_sid = SidGenerator.generate()
        name = "Pedro"
        location_sid = SidGenerator.generate()
        bag = Bag()

        player = Player.create(player_sid, name, location_sid, bag)

        assert player.sid == player_sid
        assert player.name == name
        assert player.location_sid == location_sid
        assert player.bag == bag
        assert player.is_active is True

    def test_player_name_cannot_be_empty(self):
        player_sid = SidGenerator.generate()
        location_sid = SidGenerator.generate()
        bag = Bag()

        with pytest.raises(ValueError, match="Player name cannot be empty"):
            Player.create(player_sid, "", location_sid, bag)

    def test_player_can_move_to_new_location(self):
        player_sid = SidGenerator.generate()
        original_location_sid = SidGenerator.generate()
        new_location_sid = SidGenerator.generate()
        player = Player.create(player_sid, "Pedro", original_location_sid, Bag())

        player.move_to_location(new_location_sid)

        assert player.location_sid == new_location_sid

    def test_player_can_quit_game(self):
        player = Player.create(SidGenerator.generate(), "Pedro", SidGenerator.generate(), Bag())

        player.quit_game()

        assert player.is_active is False
