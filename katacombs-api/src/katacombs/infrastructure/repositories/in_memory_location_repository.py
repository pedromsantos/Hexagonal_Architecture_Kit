
from ...domain.entities.item import Item
from ...domain.entities.location import Location
from ...domain.repositories.location_repository import LocationRepository
from ...domain.value_objects import Action, Direction, Sid


class InMemoryLocationRepository(LocationRepository):
    """Driven Adapter - In-memory implementation of LocationRepository
    Handles location persistence and provides a starting location
    """

    def __init__(self):
        self._locations: dict[Sid, Location] = {}
        self._initialize_starting_location()

    def _initialize_starting_location(self):
        """Create the default starting location for the game"""
        starting_sid = Sid.generate()
        starting_location = Location(
            sid=starting_sid,
            description="You are in the entrance hall of the ancient Katacombs. "
                       "Torches flicker on the stone walls, casting dancing shadows. "
                       "You can feel a cool breeze coming from deeper in the tunnels."
        )

        # Add some basic exits
        starting_location.add_exit(Direction.NORTH, Sid.generate())
        starting_location.add_exit(Direction.EAST, Sid.generate())

        # Add a starting item
        torch = Item(
            sid=Sid.generate(),
            name="Torch",
            description="A flickering torch that provides light in the darkness",
            available_actions=[Action.PICK, Action.USE]
        )
        starting_location.add_item(torch)

        self._locations[starting_sid] = starting_location
        self._starting_location_sid = starting_sid

    def find_by_sid(self, location_sid: Sid) -> Location | None:
        """Find location by SID"""
        return self._locations.get(location_sid)

    def find_starting_location(self) -> Location | None:
        """Get the starting location for new players"""
        return self._locations.get(self._starting_location_sid)

    def save(self, location: Location) -> None:
        """Save location to in-memory storage"""
        self._locations[location.sid] = location
