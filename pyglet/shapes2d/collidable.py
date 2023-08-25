"""2D collison detection.

The module provides classes for 2D collision dection.
"""

import math
from abc import ABC, abstractmethod
from typing import List

from pyglet.customtypes import Point2D, number


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


class CollisionShapeBase(ABC):
    """Base class for all collidable shape objects."""

    _x: number = 0
    _y: number = 0
    _anchor_x: number = 0
    _anchor_y: number = 0
    _rotation: number = 0
    _shape_name: str = "base"

    @abstractmethod
    def __contains__(self, point: Point2D) -> bool:
        """Test whether a point is inside a collidable shape.

        :param Point2D point:
            The point.

        :trype: bool
        """
        raise NotImplementedError(
            f"The `in` operator is not supported for {self.__class__.__name__}"
        )

    def is_collide(self, other: "CollisionShapeBase") -> bool:
        """Test whether two shapes are collided.

        :param CollisionShapeBase other:
            A second shape that needs to be detected with this shape.

        :rtype: bool
        """
        method = f"collide_with_{self._shape_name}"
        if hasattr(self, method) and callable(getattr(self, method)):
            return getattr(self, method)(other)
        method = f"collide_with_{other._shape_name}"
        if hasattr(other, method) and callable(getattr(other, method)):
            return getattr(other, method)(self)
        raise TypeError(
            "Cannot perform collision detection between "
            f"{self.__class__.__name} and {other.__class__.__name__}"
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

        :param number x:
            X coordinate of the sprite.
        :param number y:
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

        :param number x:
            X coordinate of the anchor point.
        :param number y:
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


class CollisionCircle(CollisionShapeBase):
    _shape_name = "circle"

    def __init__(self, x: number, y: number, radius: number) -> None:
        self._x = x
        self._y = y
        self._radius = radius

    def __contains__(self, point: Point2D) -> bool:
        point = rotate_point((self._x, self._y), point, math.radians(self._rotation))
        center = (self._x - self._anchor_x, self._y - self._anchor_y)
        return math.dist(center, point) < self._radius

    def collide_with_circle(self, other: "CollisionCircle") -> bool:
        center1 = (self._x - self._anchor_x, self._y - self._anchor_y)
        center2 = (other.x - other.anchor_x, other.y - other.anchor_y)
        length = self._radius + other.radius
        return math.dist(center1, center2) < length

    @property
    def radius(self) -> number:
        """The radius of the circle.

        :type: number
        """
        return self._radius

    @radius.setter
    def radius(self, value: number) -> None:
        self._radius = value


class CollisionEllipse(CollisionShapeBase):
    _shape_name = "ellipse"

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


class CollisionRectangle(CollisionShapeBase):
    _shape_name = "rectangle"

    def __init__(self, x: number, y: number, width: number, height: number):
        self._x = x
        self._y = y
        self._width = width
        self._height = height

    def __contains__(self, point: Point2D) -> bool:
        point = rotate_point((self._x, self._y), point, math.radians(self._rotation))
        x, y = self._x - self._anchor_x, self._y - self._anchor_y
        return x < point[0] < x + self._width and y < point[1] < y + self._height

    @property
    def width(self) -> number:
        """The width of the rectangle.

        :type: number
        """
        return self._width

    @width.setter
    def width(self, value: number) -> None:
        self._width = value

    @property
    def height(self) -> number:
        """The height of the rectangle.

        :type: number
        """
        return self._height

    @height.setter
    def height(self, value: number) -> None:
        self._height = value


class CollisionPolygon(CollisionShapeBase):
    _shape_name = "polygon"

    def __init__(self, *coordinates: Point2D) -> None:
        self._coordinates: List[Point2D] = list(coordinates)

    def __contains__(self, point: Point2D) -> bool:
        point = rotate_point(self._coordinates[0], point, math.radians(self._rotation))
        coords = self._coordinates + [self._coordinates[0]]
        coords = [
            (point[0] - self._anchor_x, point[1] - self._anchor_y) for point in coords
        ]
        return point_in_polygon(coords, point)

    @property
    def coordinates(self) -> List[Point2D]:
        """The coordinates for each point in the polygon.

        :type: List[Point2D]
        """
        return self._coordinates


__all__ = (
    "rotate_point",
    "point_in_polygon",
    "CollisionShapeBase",
    "CollisionCircle",
    "CollisionEllipse",
    "CollisionRectangle",
    "CollisionPolygon",
)
