from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from ...application.use_cases.start_game import StartGameUseCase
from ...application.dtos.start_game_dto import StartGameCommand
from ...infrastructure.repositories.in_memory_player_repository import InMemoryPlayerRepository
from ...infrastructure.repositories.in_memory_location_repository import InMemoryLocationRepository


class StartGameRequest(BaseModel):
    name: str
    sid: str


class PlayerResponse(BaseModel):
    sid: str
    name: str
    location: dict
    bag: dict


class ErrorResponse(BaseModel):
    error: str


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application
    This is a driving adapter that handles HTTP concerns
    """
    app = FastAPI(title="Katacombs API", version="1.0.0")

    # Dependency injection - in a real app, this would be more sophisticated
    def get_start_game_use_case() -> StartGameUseCase:
        player_repo = InMemoryPlayerRepository()
        location_repo = InMemoryLocationRepository()
        return StartGameUseCase(player_repo, location_repo)

    @app.post("/game/player", status_code=201, response_model=PlayerResponse)
    async def start_game(
        request: StartGameRequest,
        use_case: StartGameUseCase = Depends(get_start_game_use_case)
    ) -> PlayerResponse:
        """
        Start a new game with a new player
        Driving adapter - converts HTTP requests to domain commands
        """
        try:
            # Validate request
            if not request.name or not request.name.strip():
                raise HTTPException(status_code=400, detail="Player name cannot be empty")

            # Convert HTTP request to domain command
            command = StartGameCommand(player_name=request.name, player_sid=request.sid)

            # Execute use case
            result = use_case.execute(command)

            # Handle use case response
            if not result.success:
                raise HTTPException(status_code=400, detail=result.error_message)

            # Convert domain objects to HTTP response
            player = result.player
            return PlayerResponse(
                sid=str(player.sid.value),
                name=player.name,
                location={
                    "description": player.location.description,
                    "exits": [direction.value for direction in player.location.get_available_directions()],
                    "items": [
                        {
                            "sid": str(item.sid.value),
                            "name": item.name,
                            "description": item.description
                        }
                        for item in player.location.items
                    ]
                },
                bag={
                    "items": [
                        {
                            "sid": str(item.sid.value),
                            "name": item.name,
                            "description": item.description
                        }
                        for item in player.bag.items
                    ]
                }
            )

        except HTTPException:
            # Re-raise HTTPExceptions as-is
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return app