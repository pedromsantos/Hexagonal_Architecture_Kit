from src.game.domain.player import Sid
from src.game.domain.world import Action, Direction, Item, Location, World, WorldBuilder
from src.game.infrastructure.repositories.in_memory_world_repository import (
    InMemoryWorldRepository,
)


class TestWorldRepository:
    """INTEGRATION TEST: World Repository Implementation
    Tests the driven adapter implementation with a read-only world
    """

    def test_repository_with_custom_world(self):
        # Arrange - Create a custom world with known locations
        builder = WorldBuilder()
        test_location_sid = Sid.generate()
        test_location = Location(test_location_sid, "A test room")

        # Add item and exit to test location
        item = Item(Sid.generate(), "Key", "A rusty key", [Action.PICK])
        test_location.add_item(item)
        test_location.add_exit(Direction.NORTH, Sid.generate())

        builder.add_location(test_location)
        builder.set_starting_location(test_location_sid)
        world = builder._build()

        repo = InMemoryWorldRepository(world)

        # Act
        world = repo.get_world()
        retrieved_location = world.get_location(test_location_sid)

        # Assert
        assert retrieved_location is not None
        assert retrieved_location.sid == test_location.sid
        assert retrieved_location.description == test_location.description
        assert len(retrieved_location.items) == 1
        assert retrieved_location.items[0].name == "Key"
        assert Direction.NORTH in retrieved_location.exits

    def test_find_starting_location_with_default_world(self):
        # Arrange
        repo = InMemoryWorldRepository()

        # Act
        world = repo.get_world()
        starting_location = world.get_starting_location()

        # Assert
        assert starting_location is not None
        assert starting_location.description is not None
        assert "entrance hall" in starting_location.description.lower()

    def test_find_starting_location_with_custom_world(self):
        # Arrange - Create custom world with known starting location
        builder = WorldBuilder()
        starting_sid = Sid.generate()
        starting_location = Location(starting_sid, "Custom starting room")

        builder.add_location(starting_location)
        builder.set_starting_location(starting_sid)
        world = builder._build()

        repo = InMemoryWorldRepository(world)

        # Act
        world = repo.get_world()
        retrieved_starting = world.get_starting_location()

        # Assert
        assert retrieved_starting is not None
        assert retrieved_starting.sid == starting_sid
        assert retrieved_starting.description == "Custom starting room"

    def test_get_world_returns_complete_world(self):
        # Arrange
        repo = InMemoryWorldRepository()

        # Act
        world = repo.get_world()

        # Assert
        assert world is not None
        assert isinstance(world, World)
        assert world.get_starting_location() is not None

    def test_default_world_structure(self):
        # Arrange
        repo = InMemoryWorldRepository()

        # Act
        world = repo.get_world()
        starting_location = world.get_starting_location()

        # Assert - Verify the default world has expected structure
        assert starting_location is not None
        assert Direction.NORTH in starting_location.exits
        assert Direction.EAST in starting_location.exits
        assert len(starting_location.items) == 1
        assert starting_location.items[0].name == "Torch"
