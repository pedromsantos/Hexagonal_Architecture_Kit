from dataclasses import dataclass


@dataclass
class ItemData:
    """Item data for response"""

    sid: str
    name: str
    description: str


@dataclass
class LocationData:
    """Location data for response"""

    description: str
    exits: list[str]
    items: list[ItemData]


@dataclass
class BagData:
    """Bag data for response"""

    items: list[ItemData]


@dataclass
class PlayerData:
    """Player data for response"""

    sid: str
    name: str
    location: LocationData
    bag: BagData


@dataclass
class StartGameCommand:
    """Command to start a new game"""

    player_name: str
    player_sid: str


@dataclass
class StartGameResponse:
    """Response after starting a new game"""

    success: bool
    player_data: PlayerData | None = None
    error_message: str | None = None

    @classmethod
    def success_response(cls, player_data: PlayerData) -> "StartGameResponse":
        return cls(success=True, player_data=player_data)

    @classmethod
    def error_response(cls, error_message: str) -> "StartGameResponse":
        return cls(success=False, error_message=error_message)
