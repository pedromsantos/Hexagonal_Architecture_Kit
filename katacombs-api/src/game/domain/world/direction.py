from enum import Enum


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"

    def __str__(self) -> str:
        return self.value
