from ...domain.player import Bag, Player, PlayerRepository, Sid
from ...domain.world import WorldRepository
from .start_game_dto import (
    BagData,
    ItemData,
    LocationData,
    PlayerData,
    StartGameCommand,
    StartGameResponse,
)


class StartGameCommandHandler:
    """Command Handler - Start a new game (WRITE-SIDE)

    Orchestrates the creation of a new player and places them in the starting location.
    Contains NO business logic - only orchestration.

    IMPORTANT: This is a COMMAND handler for write operations.
    For read operations (queries), use query handlers.
    """

    def __init__(
        self,
        player_repository: PlayerRepository,
        world_repository: WorldRepository,
    ) -> None:
        self._player_repository = player_repository
        self._world_repository = world_repository

    def execute(self, command: StartGameCommand) -> StartGameResponse:
        """Execute the start game use case"""
        try:
            world = self._world_repository.get_world()
            starting_location = world.get_starting_location()
            if not starting_location:
                return StartGameResponse.error_response("No starting location found")

            player_sid = Sid(command.player_sid)
            empty_bag = Bag()
            player = Player.create(
                player_sid, command.player_name, starting_location.sid, empty_bag
            )

            self._player_repository.save(player)

            player_data = self._convert_player_to_data(player, world)
            return StartGameResponse.success_response(player_data)

        except ValueError as e:
            return StartGameResponse.error_response(str(e))
        except (RuntimeError, OSError, KeyError) as e:
            error_msg = f"Failed to start game: {e!s}"
            return StartGameResponse.error_response(error_msg)

    def _convert_player_to_data(self, player: Player, world) -> PlayerData:
        """Convert domain Player to PlayerData DTO

        Args:
            player: The Player aggregate
            world: The World aggregate (needed to fetch location and item details)
        """

        location = world.get_location(player.location_sid)
        if not location:
            msg = f"Location not found for player: {player.location_sid}"
            raise ValueError(msg)

        location_items = [
            ItemData(sid=str(item.sid.value), name=item.name, description=item.description)
            for item in location.items
        ]

        location_data = LocationData(
            description=location.description,
            exits=[direction.value for direction in location.get_available_directions()],
            items=location_items,
        )

        bag_items = []
        for item_sid in player.bag.item_sids:
            item = world.get_item_by_sid(item_sid)
            if item:
                bag_items.append(
                    ItemData(sid=str(item.sid.value), name=item.name, description=item.description)
                )

        bag_data = BagData(items=bag_items)

        return PlayerData(
            sid=str(player.sid.value), name=player.name, location=location_data, bag=bag_data
        )
