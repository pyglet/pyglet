import math
from abc import ABC, abstractmethod
from typing import List

from pyglet.customtypes import number, Point2D


def rotate_point(center: Point2D, point: Point2D, angle: number) -> Point2D:
    prev_angle = math.atan2(point[1] - center[1], point[0] - center[0])
    now_angle = prev_angle + angle
    r = math.dist(point, center)
    return (center[0] + r * math.cos(now_angle), center[1] + r * math.sin(now_angle))


def point_in_polygon(polygon: List[Point2D], point: Point2D) -> bool:
    """Raycasting Algorithm to find out whether a point is in a given polygon.

    Copy from https://www.algorithms-and-technologies.com/point_in_polygon/python
    """
    odd = False
    i = 0
    j = len(polygon) - 1
    while i < len(polygon) - 1:
        i = i + 1
        if ((polygon[i][1] > point[1]) != (polygon[j][1] > point[1])) and (
            point[0]
            < (
                (polygon[j][0] - polygon[i][0])
                * (point[1] - polygon[i][1])
                / (polygon[j][1] - polygon[i][1])
            )
            + polygon[i][0]
        ):
            odd = not odd
        j = i
    return odd


class CollisonShapeBase(ABC):
    """Base class for all collidable shape objects."""

    _x: number = 0
    _y: number = 0
    _anchor_x: number = 0
    _anchor_y: number = 0
    _rotation: number = 0

    @abstractmethod
    def __contains__(self, point: Point2D) -> bool:
        raise NotImplementedError(
            f"The `in` operator is not supported for {self.__class__.__name__}"
        )

    @property
    def x(self) -> number:
        """X coordinate of the shape.

        :type: number
        """
        return self._x

    @x.setter
    def x(self, value: number) -> None:
        self._x = value

    @property
    def y(self) -> number:
        """Y coordinate of the shape.

        :type: number
        """
        return self._y

    @y.setter
    def y(self, value: number) -> None:
        self._y = value

    @property
    def position(self) -> Point2D:
        """The (x, y) coordinates of the shape, as a tuple.

        :Parameters:
            `x` : number
                X coordinate of the sprite.
            `y` : number
                Y coordinate of the sprite.
        """
        return self._x, self._y

    @position.setter
    def position(self, values: Point2D) -> None:
        self._x, self._y = values

    @property
    def anchor_x(self) -> number:
        """The X coordinate of the anchor point

        :type: number
        """
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, value: number) -> None:
        self._anchor_x = value

    @property
    def anchor_y(self) -> number:
        """The Y coordinate of the anchor point

        :type: number
        """
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, value: number) -> None:
        self._anchor_y = value

    @property
    def anchor_position(self) -> Point2D:
        """The (x, y) coordinates of the anchor point, as a tuple.

        :Parameters:
            `x` : number
                X coordinate of the anchor point.
            `y` : number
                Y coordinate of the anchor point.
        """
        return self._anchor_x, self._anchor_y

    @anchor_position.setter
    def anchor_position(self, values: Point2D) -> None:
        self._anchor_x, self._anchor_y = values

    @property
    def rotation(self) -> number:
        """Clockwise rotation of the shape, in degrees.

        The shape will be rotated about its (anchor_x, anchor_y)
        position.

        :type: number
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: number) -> None:
        self._rotation = rotation


class CollisonCircle(CollisonShapeBase):
    def __init__(self, x: number, y: number, radius: number) -> None:
        self._x = x
        self._y = y
        self._radius = radius

    def __contains__(self, point: Point2D) -> bool:
        center = (self._x - self._anchor_x, self._y - self._anchor_y)
        return math.dist(center, point) < self._radius

    @property
    def radius(self) -> number:
        """The radius of the circle.

        :type: number
        """
        return self._radius

    @radius.setter
    def radius(self, value: number) -> None:
        self._radius = value


class CollisonEllipse(CollisonShapeBase):
    def __init__(self, x: number, y: number, a: number, b: number) -> None:
        self._x = x
        self._y = y
        self._a = a
        self._b = b

    def __contains__(self, point: Point2D) -> bool:
        point = rotate_point((self._x, self._y), point, math.radians(self._rotation))
        # Since directly testing whether a point is inside an ellipse is more
        # complicated, it is more convenient to transform it into a circle.
        point = (self._b / self._a * point[0], point[1])
        center = (
            self._b / self._a * (self._x - self._anchor_x),
            self._y - self._anchor_y,
        )
        return math.dist(center, point) < self._b

    @property
    def a(self) -> number:
        """The semi-major axes of the ellipse.

        :type: number
        """
        return self._a

    @a.setter
    def a(self, value: number) -> None:
        self._a = value

    @property
    def b(self) -> number:
        """The semi-minor axes of the ellipse.

        :type: number
        """
        return self._b

    @b.setter
    def b(self, value: number) -> None:
        self._b = value


class CollisonPolygon(CollisonShapeBase):
    def __init__(self, *coordinates: Point2D) -> None:
        self._coordinates: List[Point2D] = list(coordinates)

    def __contains__(self, point: Point2D) -> bool:
        point = rotate_point(self._coordinates[0], point, math.radians(self._rotation))
        coords = self._coordinates + [self._coordinates[0]]
        coords = [
            (point[0] - self._anchor_x, point[1] - self._anchor_y) for point in coords
        ]
        return point_in_polygon(coords, point)


__all__ = (
    "rotate_point",
    "point_in_polygon",
    "CollisonShapeBase",
    "CollisonCircle",
    "CollisonEllipse",
    "CollisonPolygon",
)
