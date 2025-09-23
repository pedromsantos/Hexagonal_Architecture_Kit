import pytest

from src.game.domain.player import Sid
from src.game.domain.world import Location, World


class TestWorld:
    """UNIT TEST: World Entity Domain Behavior
    Tests the World aggregate root business logic and invariants
    """

    def test_world_can_be_created_with_locations_and_starting_location(self):
        # Arrange
        location_sid = Sid.generate()
        location = Location(location_sid, "Test location")
        locations = {location_sid: location}

        # Act
        world = World(locations, location_sid)

        # Assert
        assert world.starting_location_sid == location_sid
        assert world.has_location(location_sid)
        assert world.get_location(location_sid) == location

    def test_world_validates_starting_location_exists(self):
        # Arrange
        location_sid = Sid.generate()
        invalid_starting_sid = Sid.generate()
        location = Location(location_sid, "Test location")
        locations = {location_sid: location}

        # Act & Assert
        with pytest.raises(ValueError, match="Starting location .* not found in world"):
            World(locations, invalid_starting_sid)

    def test_get_starting_location_returns_correct_location(self):
        # Arrange
        location_sid = Sid.generate()
        location = Location(location_sid, "Starting location")
        locations = {location_sid: location}
        world = World(locations, location_sid)

        # Act
        starting_location = world.get_starting_location()

        # Assert
        assert starting_location == location
        assert starting_location.description == "Starting location"

    def test_get_location_returns_none_for_nonexistent_location(self):
        # Arrange
        location_sid = Sid.generate()
        nonexistent_sid = Sid.generate()
        location = Location(location_sid, "Test location")
        locations = {location_sid: location}
        world = World(locations, location_sid)

        # Act
        result = world.get_location(nonexistent_sid)

        # Assert
        assert result is None

    def test_has_location_returns_true_for_existing_location(self):
        # Arrange
        location_sid = Sid.generate()
        location = Location(location_sid, "Test location")
        locations = {location_sid: location}
        world = World(locations, location_sid)

        # Act & Assert
        assert world.has_location(location_sid) is True

    def test_has_location_returns_false_for_nonexistent_location(self):
        # Arrange
        location_sid = Sid.generate()
        nonexistent_sid = Sid.generate()
        location = Location(location_sid, "Test location")
        locations = {location_sid: location}
        world = World(locations, location_sid)

        # Act & Assert
        assert world.has_location(nonexistent_sid) is False

    def test_get_all_locations_returns_defensive_copy(self):
        # Arrange
        location_sid = Sid.generate()
        location = Location(location_sid, "Test location")
        locations = {location_sid: location}
        world = World(locations, location_sid)

        # Act
        all_locations = world.get_all_locations()

        # Assert
        assert all_locations == locations
        assert all_locations is not world._locations  # Defensive copy

        # Modify returned copy should not affect world
        all_locations.clear()
        assert world.has_location(location_sid)  # Original unchanged

    def test_world_creates_defensive_copy_of_input_locations(self):
        # Arrange
        location_sid = Sid.generate()
        location = Location(location_sid, "Test location")
        original_locations = {location_sid: location}
        world = World(original_locations, location_sid)

        # Act - Modify original dict
        original_locations.clear()

        # Assert - World should be unaffected
        assert world.has_location(location_sid)
        assert world.get_location(location_sid) == location

    def test_world_with_multiple_locations(self):
        # Arrange
        location1_sid = Sid.generate()
        location2_sid = Sid.generate()
        location3_sid = Sid.generate()

        location1 = Location(location1_sid, "First location")
        location2 = Location(location2_sid, "Second location")
        location3 = Location(location3_sid, "Third location")

        locations = {
            location1_sid: location1,
            location2_sid: location2,
            location3_sid: location3,
        }

        # Act
        world = World(locations, location2_sid)  # Start at second location

        # Assert
        assert world.starting_location_sid == location2_sid
        assert world.get_starting_location() == location2
        assert world.has_location(location1_sid)
        assert world.has_location(location2_sid)
        assert world.has_location(location3_sid)
        assert len(world.get_all_locations()) == 3