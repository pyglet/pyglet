import math
from abc import ABC, abstractmethod
from typing import List, Tuple, Union


def rotate_point(center: Tuple[int, int], point: Tuple[int, int], angle: float) -> Tuple[int, int]:
    prev_angle = math.atan2(point[1] - center[1], point[0] - center[0])
    now_angle = prev_angle + angle
    r = math.dist(point, center)
    return (center[0] + r * math.cos(now_angle), center[1] + r * math.sin(now_angle))


def point_in_polygon(polygon: List[Tuple[int, int]], point: Tuple[int, int]) -> bool:
    """Raycasting Algorithm to find out whether a point is in a given polygon.

    Copy from https://www.algorithms-and-technologies.com/point_in_polygon/python
    """
    odd = False
    i = 0
    j = len(polygon) - 1
    while i < len(polygon) - 1:
        i = i + 1
        if (((polygon[i][1] > point[1]) != (polygon[j][1] > point[1])) and (point[0] < (
        (polygon[j][0] - polygon[i][0]) * (point[1] - polygon[i][1]) / (polygon[j][1] - polygon[i][1])) +
        polygon[i][0])):
            odd = not odd
        j = i
    return odd


class CollisonShapeBase(ABC):
    """Base class for all collidable shape objects."""
    _x = 0
    _y = 0
    _anchor_x = 0
    _anchor_y = 0
    _rotation = 0

    @abstractmethod
    def __contains__(self, point: Tuple[int, int]) –> bool:
        raise NotImplementedError(f"The `in` operator is not supported for {self.__class__.__name__}")

    @property
    def x(self):
        """X coordinate of the shape.

        :type: int or float
        """
        return self._x

    @x.setter
    def x(self, value):
        self._x = value

    @property
    def y(self):
        """Y coordinate of the shape.

        :type: int or float
        """
        return self._y

    @y.setter
    def y(self, value):
        self._y = value

    @property
    def position(self):
        """The (x, y) coordinates of the shape, as a tuple.

        :Parameters:
            `x` : int or float
                X coordinate of the sprite.
            `y` : int or float
                Y coordinate of the sprite.
        """
        return self._x, self._y

    @position.setter
    def position(self, values):
        self._x, self._y = values

    @property
    def anchor_x(self):
        """The X coordinate of the anchor point

        :type: int or float
        """
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, value):
        self._anchor_x = value

    @property
    def anchor_y(self):
        """The Y coordinate of the anchor point

        :type: int or float
        """
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, value):
        self._anchor_y = value

    @property
    def anchor_position(self):
        """The (x, y) coordinates of the anchor point, as a tuple.

        :Parameters:
            `x` : int or float
                X coordinate of the anchor point.
            `y` : int or float
                Y coordinate of the anchor point.
        """
        return self._anchor_x, self._anchor_y

    @anchor_position.setter
    def anchor_position(self, values):
        self._anchor_x, self._anchor_y = values

    @property
    def rotation(self):
        """Clockwise rotation of the shape, in degrees.

        The shape will be rotated about its (anchor_x, anchor_y)
        position.

        :type: float
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation):
        self._rotation = rotation


class CollisonPolygon(CollisonShapeBase):
    def __init__(self, *coordinates, anchor_position: Tuple[float, float]=(0, 0), rotation: float=0):
        self._coordinates = list(coordinates)
        self._anchor_x, self._anchor_y = anchor_position
        self._rotation = rotation

    def __contains__(self, point: Tuple[int, int]) –> bool:
        point = rotate_point(self._coordinates[0], point, math.radians(self._rotation))
        coords = self._coordinates + [self._coordinates[0]]
        return point_in_polygon(coords, point)

__all__ = "rotate_point", "point_in_polygon", "CollisonShapeBase", "CollisonPolygon"
