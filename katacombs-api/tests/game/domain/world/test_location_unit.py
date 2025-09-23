import pytest

from src.game.domain.player import Sid
from src.game.domain.world import Action, Direction, Item, Location


class TestLocation:
    """UNIT TEST: Location Entity Domain Behavior
    Tests the Location entity business logic and validation rules
    """

    def test_location_can_be_created_with_valid_data(self):
        # Arrange
        location_sid = Sid.generate()
        description = "A mysterious chamber"

        # Act
        location = Location(location_sid, description)

        # Assert
        assert location.sid == location_sid
        assert location.description == description
        assert location.exits == {}
        assert location.items == []

    def test_location_cannot_be_created_with_empty_description(self):
        # Arrange
        location_sid = Sid.generate()
        empty_description = ""

        # Act & Assert
        with pytest.raises(ValueError, match="Location description cannot be empty"):
            Location(location_sid, empty_description)

    def test_location_cannot_be_created_with_whitespace_only_description(self):
        # Arrange
        location_sid = Sid.generate()
        whitespace_description = "   \t\n   "

        # Act & Assert
        with pytest.raises(ValueError, match="Location description cannot be empty"):
            Location(location_sid, whitespace_description)

    def test_add_exit_creates_connection_to_destination(self):
        # Arrange
        location_sid = Sid.generate()
        destination_sid = Sid.generate()
        location = Location(location_sid, "Starting room")

        # Act
        location.add_exit(Direction.NORTH, destination_sid)

        # Assert
        assert location.exits[Direction.NORTH] == destination_sid

    def test_add_exit_can_create_exit_without_destination(self):
        # Arrange
        location_sid = Sid.generate()
        location = Location(location_sid, "Room with blocked exit")

        # Act
        location.add_exit(Direction.SOUTH, None)

        # Assert
        assert location.exits[Direction.SOUTH] is None

    def test_get_available_directions_returns_only_connected_exits(self):
        # Arrange
        location_sid = Sid.generate()
        destination_sid = Sid.generate()
        location = Location(location_sid, "Hub room")

        # Add some exits
        location.add_exit(Direction.NORTH, destination_sid)  # Connected
        location.add_exit(Direction.SOUTH, None)  # Blocked/unconnected
        location.add_exit(Direction.EAST, Sid.generate())  # Connected

        # Act
        available_directions = location.get_available_directions()

        # Assert
        assert Direction.NORTH in available_directions
        assert Direction.EAST in available_directions
        assert Direction.SOUTH not in available_directions  # None destination excluded
        assert len(available_directions) == 2

    def test_get_available_directions_returns_empty_list_when_no_exits(self):
        # Arrange
        location_sid = Sid.generate()
        location = Location(location_sid, "Isolated room")

        # Act
        available_directions = location.get_available_directions()

        # Assert
        assert available_directions == []

    def test_add_item_adds_item_to_location(self):
        # Arrange
        location_sid = Sid.generate()
        location = Location(location_sid, "Treasure room")

        item_sid = Sid.generate()
        item = Item(item_sid, "Golden key", "A shiny golden key", [Action.PICK])

        # Act
        location.add_item(item)

        # Assert
        assert item in location.items
        assert len(location.items) == 1

    def test_add_multiple_items_maintains_order(self):
        # Arrange
        location_sid = Sid.generate()
        location = Location(location_sid, "Storage room")

        item1 = Item(Sid.generate(), "Sword", "A sharp sword", [Action.PICK])
        item2 = Item(Sid.generate(), "Shield", "A sturdy shield", [Action.PICK])
        item3 = Item(Sid.generate(), "Potion", "A healing potion", [Action.USE])

        # Act
        location.add_item(item1)
        location.add_item(item2)
        location.add_item(item3)

        # Assert
        assert location.items == [item1, item2, item3]
        assert len(location.items) == 3

    def test_location_with_multiple_exits_and_items(self):
        # Arrange
        location_sid = Sid.generate()
        location = Location(location_sid, "Central chamber")

        # Add exits in all directions
        north_sid = Sid.generate()
        south_sid = Sid.generate()
        east_sid = Sid.generate()

        location.add_exit(Direction.NORTH, north_sid)
        location.add_exit(Direction.SOUTH, south_sid)
        location.add_exit(Direction.EAST, east_sid)
        location.add_exit(Direction.WEST, None)  # Blocked exit

        # Add items
        torch = Item(Sid.generate(), "Torch", "A burning torch", [Action.PICK, Action.USE])
        key = Item(Sid.generate(), "Key", "An old key", [Action.PICK])

        location.add_item(torch)
        location.add_item(key)

        # Act & Assert
        available_directions = location.get_available_directions()
        assert len(available_directions) == 3  # Only connected exits
        assert Direction.WEST not in available_directions  # Blocked exit excluded

        assert len(location.items) == 2
        assert torch in location.items
        assert key in location.items

    def test_location_exits_can_be_overwritten(self):
        # Arrange
        location_sid = Sid.generate()
        location = Location(location_sid, "Changing room")

        original_destination = Sid.generate()
        new_destination = Sid.generate()

        # Act
        location.add_exit(Direction.NORTH, original_destination)
        assert location.exits[Direction.NORTH] == original_destination

        location.add_exit(Direction.NORTH, new_destination)  # Overwrite

        # Assert
        assert location.exits[Direction.NORTH] == new_destination
