from ...domain.world import World, WorldBuilder, WorldRepository


class InMemoryWorldRepository(WorldRepository):
    """Driven Adapter - In-memory implementation of WorldRepository

    This repository loads the complete World aggregate once and returns it.
    All world traversal and querying is handled by the World aggregate root itself.
    """

    def __init__(self, world: World | None = None) -> None:
        super().__init__()
        self._world = world or self._create_default_world()

    def _create_default_world(self) -> World:
        """Create the default world using WorldBuilder"""
        builder = WorldBuilder()
        return builder.create_starter_world()

    def get_world(self) -> World:
        """Get the complete world aggregate with all locations loaded"""
        return self._world
