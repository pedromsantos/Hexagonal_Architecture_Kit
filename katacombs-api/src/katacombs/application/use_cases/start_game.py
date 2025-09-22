from ...domain.entities.bag import Bag
from ...domain.entities.player import Player
from ...domain.repositories.location_repository import LocationRepository
from ...domain.repositories.player_repository import PlayerRepository
from ...domain.value_objects import Sid
from ..dtos.start_game_dto import (
    BagData,
    ItemData,
    LocationData,
    PlayerData,
    StartGameCommand,
    StartGameResponse,
)


class StartGameUseCase:
    """Use Case - Start a new game
    Orchestrates the creation of a new player and places them in the starting location
    Contains NO business logic - only orchestration
    """

    def __init__(
        self,
        player_repository: PlayerRepository,
        location_repository: LocationRepository,
    ) -> None:
        self._player_repository = player_repository
        self._location_repository = location_repository

    def execute(self, command: StartGameCommand) -> StartGameResponse:
        """Execute the start game use case"""
        try:
            # Get the starting location
            starting_location = self._location_repository.find_starting_location()
            if not starting_location:
                return StartGameResponse.error_response("No starting location found")

            # Create a new player with provided SID (domain logic is in the Player.create method)
            player_sid = Sid(command.player_sid)  # Validate the provided SID
            empty_bag = Bag()
            player = Player.create(player_sid, command.player_name, starting_location, empty_bag)

            # Save the player
            self._player_repository.save(player)

            # Convert domain objects to response data
            player_data = self._convert_player_to_data(player)
            return StartGameResponse.success_response(player_data)

        except ValueError as e:
            return StartGameResponse.error_response(str(e))
        except (RuntimeError, OSError, KeyError) as e:
            error_msg = f"Failed to start game: {e!s}"
            return StartGameResponse.error_response(error_msg)

    def _convert_player_to_data(self, player: Player) -> PlayerData:
        """Convert domain Player to PlayerData DTO"""
        # Convert location items to ItemData
        location_items = [
            ItemData(sid=str(item.sid.value), name=item.name, description=item.description)
            for item in player.location.items
        ]

        # Convert location to LocationData
        location_data = LocationData(
            description=player.location.description,
            exits=[direction.value for direction in player.location.get_available_directions()],
            items=location_items,
        )

        # Convert bag items to ItemData
        bag_items = [
            ItemData(sid=str(item.sid.value), name=item.name, description=item.description)
            for item in player.bag.items
        ]

        # Convert bag to BagData
        bag_data = BagData(items=bag_items)

        # Convert player to PlayerData
        return PlayerData(
            sid=str(player.sid.value), name=player.name, location=location_data, bag=bag_data
        )
