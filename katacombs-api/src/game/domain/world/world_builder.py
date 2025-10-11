from __future__ import annotations

from ..player.sid import Sid
from .action import Action
from .direction import Direction
from .item import Item
from .location import Location
from .world import World


class WorldBuilder:
    """Builder for constructing the game world

    Encapsulates all world creation logic and business rules.
    Provides methods to build different types of worlds (starter, full, custom).

    IMPORTANT: All SIDs must be provided by external systems.
    The domain does not generate IDs - this is an infrastructure concern.
    """

    def __init__(self) -> None:
        self._locations: dict[Sid, Location] = {}
        self._starting_location_sid: Sid | None = None

    def create_starter_world(
        self,
        entrance_sid: Sid,
        north_corridor_sid: Sid,
        east_chamber_sid: Sid,
        torch_sid: Sid,
    ) -> World:
        """Create the default starter world with entrance hall and basic setup

        Args:
            entrance_sid: SID for the entrance hall location (provided by external system)
            north_corridor_sid: SID for the north corridor location (provided by external system)
            east_chamber_sid: SID for the east chamber location (provided by external system)
            torch_sid: SID for the torch item (provided by external system)

        Returns:
            The constructed starter world
        """
        self._clear()

        # Create the entrance hall (starting location)
        entrance_description = (
            "You are in the entrance hall of the ancient Katacombs. "
            "Torches flicker on the stone walls, casting dancing shadows. "
            "You can feel a cool breeze coming from deeper in the tunnels."
        )
        entrance_location = Location(sid=entrance_sid, description=entrance_description)

        # Create connected locations
        north_corridor = Location(
            sid=north_corridor_sid,
            description="A narrow stone corridor extends to the north. The walls are carved with ancient symbols."
        )

        east_chamber = Location(
            sid=east_chamber_sid,
            description="A small chamber with a low ceiling. Water drips steadily from somewhere above."
        )

        # Connect the locations
        entrance_location.add_exit(Direction.NORTH, north_corridor_sid)
        entrance_location.add_exit(Direction.EAST, east_chamber_sid)
        north_corridor.add_exit(Direction.SOUTH, entrance_sid)
        east_chamber.add_exit(Direction.WEST, entrance_sid)

        # Add starting items
        torch = Item(
            sid=torch_sid,
            name="Torch",
            description="A flickering torch that provides light in the darkness",
            available_actions=[Action.PICK, Action.USE],
        )
        entrance_location.add_item(torch)

        # Add the locations to the world
        self._locations[entrance_sid] = entrance_location
        self._locations[north_corridor_sid] = north_corridor
        self._locations[east_chamber_sid] = east_chamber
        self._starting_location_sid = entrance_sid

        return self._build()

    def add_location(self, location: Location) -> WorldBuilder:
        """Add a location to the world being built"""
        self._locations[location.sid] = location
        return self

    def set_starting_location(self, location_sid: Sid) -> WorldBuilder:
        """Set the starting location for the world"""
        self._starting_location_sid = location_sid
        return self

    def _build(self) -> World:
        """Build and return the final World entity"""
        if self._starting_location_sid is None:
            raise ValueError("Starting location must be set before building world")

        return World(
            locations=self._locations,
            starting_location_sid=self._starting_location_sid
        )

    def _clear(self) -> None:
        """Clear all current world data"""
        self._locations.clear()
        self._starting_location_sid = None