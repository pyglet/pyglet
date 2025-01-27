from enum import auto, Enum


class GeometryMode(Enum):
    POINTS = auto()
    LINES = auto()
    LINE_STRIP = auto()
    TRIANGLES = auto()
    TRIANGLE_STRIP = auto()
    TRIANGLE_FAN = auto()