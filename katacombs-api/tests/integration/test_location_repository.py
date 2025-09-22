from src.katacombs.domain.entities.item import Item
from src.katacombs.domain.entities.location import Location
from src.katacombs.domain.value_objects import Action, Direction, Sid
from src.katacombs.infrastructure.repositories.in_memory_location_repository import (
    InMemoryLocationRepository,
)


class TestLocationRepository:
    """INTEGRATION TEST: Location Repository Implementation
    Tests the driven adapter implementation with real storage
    """

    def test_save_and_find_location_by_sid(self):
        # Arrange
        repo = InMemoryLocationRepository()
        location_sid = Sid.generate()
        location = Location(location_sid, "A dark room")

        # Act
        repo.save(location)
        retrieved_location = repo.find_by_sid(location_sid)

        # Assert
        assert retrieved_location is not None
        assert retrieved_location.sid == location.sid
        assert retrieved_location.description == location.description

    def test_find_starting_location(self):
        # Arrange
        repo = InMemoryLocationRepository()

        # The repository should provide a starting location
        # Act
        starting_location = repo.find_starting_location()

        # Assert
        assert starting_location is not None
        assert starting_location.description is not None

    def test_location_with_items_and_exits(self):
        # Arrange
        repo = InMemoryLocationRepository()
        location_sid = Sid.generate()
        location = Location(location_sid, "Room with items")

        # Add an item and exit
        item = Item(Sid.generate(), "Key", "A rusty key", [Action.PICK])
        location.add_item(item)
        location.add_exit(Direction.NORTH, Sid.generate())

        # Act
        repo.save(location)
        retrieved_location = repo.find_by_sid(location_sid)

        # Assert
        assert retrieved_location is not None
        assert len(retrieved_location.items) == 1
        assert retrieved_location.items[0].name == "Key"
        assert Direction.NORTH in retrieved_location.exits
