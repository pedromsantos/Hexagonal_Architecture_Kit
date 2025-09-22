from dataclasses import dataclass
from typing import Optional

from ...domain.entities.player import Player


@dataclass
class StartGameCommand:
    """Command to start a new game"""
    player_name: str


@dataclass
class StartGameResponse:
    """Response after starting a new game"""
    success: bool
    player: Optional[Player] = None
    error_message: Optional[str] = None

    @classmethod
    def success_response(cls, player: Player) -> "StartGameResponse":
        return cls(success=True, player=player)

    @classmethod
    def error_response(cls, error_message: str) -> "StartGameResponse":
        return cls(success=False, error_message=error_message)