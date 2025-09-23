from abc import ABC, abstractmethod

from .world import World


class WorldRepository(ABC):
    """Driven Port - Repository interface for World aggregate

    Repositories handle persistence of complete aggregates, not individual entities within them.
    The World aggregate root provides methods to traverse and query the world hierarchy.
    """

    @abstractmethod
    def get_world(self) -> World:
        """Get the complete world aggregate with all locations loaded"""
        pass
