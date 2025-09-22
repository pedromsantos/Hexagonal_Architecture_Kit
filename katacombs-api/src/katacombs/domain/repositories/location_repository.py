from abc import ABC, abstractmethod
from typing import Optional

from ..entities.location import Location
from ..value_objects import Sid


class LocationRepository(ABC):
    """
    Driven Port - Repository interface for Location entity
    This belongs in the domain layer as it represents a domain concept
    """

    @abstractmethod
    def find_by_sid(self, location_sid: Sid) -> Optional[Location]:
        pass

    @abstractmethod
    def find_starting_location(self) -> Optional[Location]:
        pass

    @abstractmethod
    def save(self, location: Location) -> None:
        pass