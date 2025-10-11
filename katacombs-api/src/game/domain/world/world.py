from __future__ import annotations

from ..player.sid import Sid
from .location import Location


class World:
    """Domain entity representing the complete game world

    A read-only container for all locations in the game world.
    World creation and modification is handled by WorldBuilder.
    """

    def __init__(self, locations: dict[Sid, Location], starting_location_sid: Sid) -> None:
        self._locations = locations.copy()  # Defensive copy
        self._starting_location_sid = starting_location_sid

        # Validate starting location exists
        if starting_location_sid not in self._locations:
            raise ValueError(f"Starting location {starting_location_sid} not found in world")

    @property
    def starting_location_sid(self) -> Sid:
        """Get the SID of the starting location"""
        return self._starting_location_sid

    def get_location(self, location_sid: Sid) -> Location | None:
        """Get a location by its SID"""
        return self._locations.get(location_sid)

    def get_starting_location(self) -> Location:
        """Get the starting location for new players"""
        return self._locations[self._starting_location_sid]

    def get_all_locations(self) -> dict[Sid, Location]:
        """Get all locations in the world (defensive copy)"""
        return self._locations.copy()

    def has_location(self, location_sid: Sid) -> bool:
        """Check if a location exists in the world"""
        return location_sid in self._locations

    def get_item_by_sid(self, item_sid: Sid):
        """Get an item by its SID from any location in the world"""
        for location in self._locations.values():
            for item in location.items:
                if item.sid == item_sid:
                    return item
        return None