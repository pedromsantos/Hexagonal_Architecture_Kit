from typing import Annotated, cast

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from ...application.dtos.start_game_dto import PlayerData, StartGameCommand
from ...application.use_cases.start_game import StartGameUseCase
from ...infrastructure.repositories.in_memory_location_repository import InMemoryLocationRepository
from ...infrastructure.repositories.in_memory_player_repository import InMemoryPlayerRepository


class StartGameRequest(BaseModel):
    name: str
    sid: str


class PlayerResponse(BaseModel):
    sid: str
    name: str
    location: dict[str, object]
    bag: dict[str, object]


class ErrorResponse(BaseModel):
    error: str


def _validate_request(request: StartGameRequest) -> None:
    """Validate start game request"""
    if not request.name or not request.name.strip():
        raise HTTPException(status_code=400, detail="Player name cannot be empty")


def _raise_error_response(error_message: str) -> None:
    """Raise HTTP exception for error response"""
    raise HTTPException(status_code=400, detail=error_message)


def _raise_server_error(message: str) -> None:
    """Raise HTTP exception for server error"""
    raise HTTPException(status_code=500, detail=message)


def _execute_start_game_command(
    use_case: StartGameUseCase, request: StartGameRequest
) -> PlayerResponse:
    """Execute start game command and return response"""
    _validate_request(request)
    command = StartGameCommand(player_name=request.name, player_sid=request.sid)
    result = use_case.execute(command)

    if not result.success:
        _raise_error_response(result.error_message or "Unknown error")

    # Handle the case where player creation failed
    if result.player_data is None:
        _raise_server_error("Player creation failed")

    # Convert DTO to HTTP response
    return _convert_player_data_to_response(cast("PlayerData", result.player_data))


def _convert_player_data_to_response(player_data: PlayerData) -> PlayerResponse:
    """Convert PlayerData DTO to HTTP response"""
    return PlayerResponse(
        sid=player_data.sid,
        name=player_data.name,
        location={
            "description": player_data.location.description,
            "exits": player_data.location.exits,
            "items": [
                {"sid": item.sid, "name": item.name, "description": item.description}
                for item in player_data.location.items
            ],
        },
        bag={
            "items": [
                {"sid": item.sid, "name": item.name, "description": item.description}
                for item in player_data.bag.items
            ]
        },
    )


def get_start_game_use_case() -> StartGameUseCase:
    """Dependency injection for start game use case"""
    player_repo = InMemoryPlayerRepository()
    location_repo = InMemoryLocationRepository()
    return StartGameUseCase(player_repo, location_repo)


async def start_game(
    request: StartGameRequest,
    use_case: Annotated[StartGameUseCase, Depends(get_start_game_use_case)],
) -> PlayerResponse:
    """Start a new game with a new player
    Driving adapter - converts HTTP requests to domain commands
    """
    try:
        return _execute_start_game_command(use_case, request)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        error_detail = f"Internal server error: {e!s}"
        raise HTTPException(status_code=500, detail=error_detail) from e


def create_app() -> FastAPI:
    """Create and configure FastAPI application
    This is a driving adapter that handles HTTP concerns
    """
    app = FastAPI(title="Katacombs API", version="1.0.0")
    _ = app.post("/game/player", status_code=201)(start_game)
    return app
