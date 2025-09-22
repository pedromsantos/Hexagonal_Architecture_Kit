from ...domain.repositories.player_repository import PlayerRepository
from ...domain.repositories.location_repository import LocationRepository
from ...domain.entities.player import Player
from ...domain.entities.bag import Bag
from ...domain.value_objects import Sid
from ..dtos.start_game_dto import StartGameCommand, StartGameResponse


class StartGameUseCase:
    """
    Use Case - Start a new game
    Orchestrates the creation of a new player and places them in the starting location
    Contains NO business logic - only orchestration
    """

    def __init__(
        self,
        player_repository: PlayerRepository,
        location_repository: LocationRepository
    ):
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

            return StartGameResponse.success_response(player)

        except ValueError as e:
            return StartGameResponse.error_response(str(e))
        except Exception as e:
            return StartGameResponse.error_response(f"Failed to start game: {str(e)}")