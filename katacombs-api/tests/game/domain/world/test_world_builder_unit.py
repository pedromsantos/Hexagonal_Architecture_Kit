import pytest

from src.game.domain.player import Sid
from src.game.domain.world import Action, Direction, Location, World, WorldBuilder
from src.game.infrastructure.sid_generator import SidGenerator


class TestWorldBuilder:
    """UNIT TEST: WorldBuilder Domain Service
    Tests the WorldBuilder business logic for world construction
    """

    def test_create_starter_world_creates_valid_world(self):
        # Arrange
        builder = WorldBuilder()
        # SIDs provided by external system (tests act as external system)
        entrance_sid = SidGenerator.generate()
        north_sid = SidGenerator.generate()
        east_sid = SidGenerator.generate()
        torch_sid = SidGenerator.generate()

        # Act
        world = builder.create_starter_world(entrance_sid, north_sid, east_sid, torch_sid)

        # Assert
        assert isinstance(world, World)
        assert world.get_starting_location() is not None

    def test_create_starter_world_has_entrance_hall(self):
        # Arrange
        builder = WorldBuilder()
        entrance_sid = SidGenerator.generate()
        north_sid = SidGenerator.generate()
        east_sid = SidGenerator.generate()
        torch_sid = SidGenerator.generate()

        # Act
        world = builder.create_starter_world(entrance_sid, north_sid, east_sid, torch_sid)
        starting_location = world.get_starting_location()

        # Assert
        assert "entrance hall" in starting_location.description.lower()
        assert "katacombs" in starting_location.description.lower()

    def test_create_starter_world_has_connected_locations(self):
        # Arrange
        builder = WorldBuilder()
        entrance_sid = SidGenerator.generate()
        north_sid = SidGenerator.generate()
        east_sid = SidGenerator.generate()
        torch_sid = SidGenerator.generate()

        # Act
        world = builder.create_starter_world(entrance_sid, north_sid, east_sid, torch_sid)
        starting_location = world.get_starting_location()

        # Assert
        available_directions = starting_location.get_available_directions()
        assert Direction.NORTH in available_directions
        assert Direction.EAST in available_directions
        assert len(available_directions) == 2

    def test_create_starter_world_locations_are_bidirectionally_connected(self):
        # Arrange
        builder = WorldBuilder()
        entrance_sid = SidGenerator.generate()
        north_sid = SidGenerator.generate()
        east_sid = SidGenerator.generate()
        torch_sid = SidGenerator.generate()

        # Act
        world = builder.create_starter_world(entrance_sid, north_sid, east_sid, torch_sid)
        starting_location = world.get_starting_location()

        # Navigate north and back
        north_destination_sid = starting_location.exits[Direction.NORTH]
        north_location = world.get_location(north_destination_sid)

        # Assert
        assert north_location is not None
        assert Direction.SOUTH in north_location.exits
        assert north_location.exits[Direction.SOUTH] == starting_location.sid

    def test_create_starter_world_has_torch_item(self):
        # Arrange
        builder = WorldBuilder()
        entrance_sid = SidGenerator.generate()
        north_sid = SidGenerator.generate()
        east_sid = SidGenerator.generate()
        torch_sid = SidGenerator.generate()

        # Act
        world = builder.create_starter_world(entrance_sid, north_sid, east_sid, torch_sid)
        starting_location = world.get_starting_location()

        # Assert
        assert len(starting_location.items) == 1
        torch = starting_location.items[0]
        assert torch.name == "Torch"
        assert Action.PICK in torch.available_actions
        assert Action.USE in torch.available_actions

    def test_builder_can_create_custom_world_with_single_location(self):
        # Arrange
        builder = WorldBuilder()
        location_sid = SidGenerator.generate()
        custom_location = Location(location_sid, "Custom test room")

        # Act
        world = builder.add_location(custom_location).set_starting_location(location_sid)._build()

        # Assert
        assert world.get_starting_location() == custom_location
        assert world.has_location(location_sid)

    def test_builder_can_create_custom_world_with_multiple_locations(self):
        # Arrange
        builder = WorldBuilder()

        location1_sid = SidGenerator.generate()
        location2_sid = SidGenerator.generate()
        location3_sid = SidGenerator.generate()

        location1 = Location(location1_sid, "First room")
        location2 = Location(location2_sid, "Second room")
        location3 = Location(location3_sid, "Third room")

        # Act
        world = (
            builder.add_location(location1)
            .add_location(location2)
            .add_location(location3)
            .set_starting_location(location2_sid)  # Start at second location
            ._build()
        )

        # Assert
        assert world.get_starting_location() == location2
        assert world.has_location(location1_sid)
        assert world.has_location(location2_sid)
        assert world.has_location(location3_sid)
        assert len(world.get_all_locations()) == 3

    def test_builder_add_location_returns_builder_for_chaining(self):
        # Arrange
        builder = WorldBuilder()
        location = Location(SidGenerator.generate(), "Test room")

        # Act
        result = builder.add_location(location)

        # Assert
        assert result is builder  # Builder pattern - returns self

    def test_builder_set_starting_location_returns_builder_for_chaining(self):
        # Arrange
        builder = WorldBuilder()
        location_sid = SidGenerator.generate()

        # Act
        result = builder.set_starting_location(location_sid)

        # Assert
        assert result is builder  # Builder pattern - returns self

    def test_builder_throws_error_when_building_without_starting_location(self):
        # Arrange
        builder = WorldBuilder()
        location = Location(SidGenerator.generate(), "Test room")
        builder.add_location(location)

        # Act & Assert
        with pytest.raises(ValueError, match="Starting location must be set before building world"):
            builder._build()

    def test_builder_throws_error_when_starting_location_not_in_world(self):
        # Arrange
        builder = WorldBuilder()
        location_sid = SidGenerator.generate()
        invalid_starting_sid = SidGenerator.generate()

        location = Location(location_sid, "Test room")
        builder.add_location(location)
        builder.set_starting_location(invalid_starting_sid)

        # Act & Assert
        with pytest.raises(ValueError, match="Starting location .* not found in world"):
            builder._build()

    def test_create_starter_world_clears_previous_data(self):
        # Arrange
        builder = WorldBuilder()

        # Add some custom data first
        custom_location = Location(SidGenerator.generate(), "Custom room")
        builder.add_location(custom_location)

        # Act
        entrance_sid = SidGenerator.generate()
        north_sid = SidGenerator.generate()
        east_sid = SidGenerator.generate()
        torch_sid = SidGenerator.generate()
        world = builder.create_starter_world(entrance_sid, north_sid, east_sid, torch_sid)

        # Assert - Should not contain the custom location
        custom_locations = [
            loc for loc in world.get_all_locations().values() if loc.description == "Custom room"
        ]
        assert len(custom_locations) == 0

        # Should contain starter world content
        starting_location = world.get_starting_location()
        assert "entrance hall" in starting_location.description.lower()

    def test_multiple_create_starter_world_calls_produce_independent_worlds(self):
        # Arrange
        builder = WorldBuilder()

        # Act
        entrance_sid1 = SidGenerator.generate()
        north_sid1 = SidGenerator.generate()
        east_sid1 = SidGenerator.generate()
        torch_sid1 = SidGenerator.generate()
        world1 = builder.create_starter_world(entrance_sid1, north_sid1, east_sid1, torch_sid1)

        entrance_sid2 = SidGenerator.generate()
        north_sid2 = SidGenerator.generate()
        east_sid2 = SidGenerator.generate()
        torch_sid2 = SidGenerator.generate()
        world2 = builder.create_starter_world(entrance_sid2, north_sid2, east_sid2, torch_sid2)

        # Assert - Worlds should have different locations with different SIDs
        world1_starting = world1.get_starting_location()
        world2_starting = world2.get_starting_location()

        assert world1_starting.sid != world2_starting.sid
        assert world1_starting.description == world2_starting.description  # Same content

    def test_builder_can_be_reused_after_building(self):
        # Arrange
        builder = WorldBuilder()

        # Build first world
        location1 = Location(SidGenerator.generate(), "First world room")
        world1 = builder.add_location(location1).set_starting_location(location1.sid)._build()

        # Build second world with same builder
        location2 = Location(SidGenerator.generate(), "Second world room")
        world2 = builder.add_location(location2).set_starting_location(location2.sid)._build()

        # Assert - Both worlds should be independent
        assert world1.get_starting_location() != world2.get_starting_location()
        assert world1.has_location(location1.sid)
        assert world2.has_location(location2.sid)

        # First world should still work
        assert world1.get_starting_location().description == "First world room"
