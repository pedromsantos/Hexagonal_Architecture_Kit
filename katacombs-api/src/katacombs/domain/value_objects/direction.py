from enum import Enum


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    UP = "up"
    DOWN = "down"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, direction: str) -> "Direction":
        for d in cls:
            if d.value == direction.lower():
                return d
        raise ValueError(f"Invalid direction: {direction}")

    def opposite(self) -> "Direction":
        opposites = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST,
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
        }
        return opposites[self]
