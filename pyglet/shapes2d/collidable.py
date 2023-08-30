"""2D collison detection.

The module provides classes for 2D collision dection.
"""

import math
from abc import ABC, abstractmethod
from typing import List

from pyglet.customtypes import Point2D, number
from pyglet.math import Vec2
from pyglet.shapes2d.util import *


class CollisionShapeBase(ABC):
    """Base class for all collidable shape objects."""

    _x: number = 0
    _y: number = 0
    _anchor_x: number = 0
    _anchor_y: number = 0
    _rotation: number = 0

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

    def _transform(self, point: Point2D) -> Point2D:
        if hasattr(self, "coordinates"):
            center = Vec2(*self._coordinates[0])
        else:
            center = Vec2(self._x, self._y)
        point = Vec2(*point) - Vec2(self._anchor_x, self._anchor_y)
        rotated = (point - center).rotate(-math.radians(self._rotation))
        return tuple(center + rotated)

    def _inverse(self, point: Point2D) -> Point2D:
        if hasattr(self, "coordinates"):
            center = Vec2(*self._coordinates[0])
        else:
            center = Vec2(self._x, self._y)
        rotated = (Vec2(*point) - center).rotate(math.radians(self._rotation))
        return tuple(rotated + center + Vec2(self._anchor_y, self._anchor_y))

    def is_collide(self, other: "CollisionShapeBase") -> bool:
        """Test whether two shapes are collided.

        :param CollisionShapeBase other:
            A second shape that needs to be detected with this shape.

        :rtype: bool
        """
        method = f"collide_with_{other.__class__.__name__}"
        if hasattr(self, method) and callable(getattr(self, method)):
            return getattr(self, method)(other)
        method = f"collide_with_{self.__class__.__name__}"
        if hasattr(other, method) and callable(getattr(other, method)):
            return getattr(other, method)(self)
        if hasattr(self, "get_polygon") and hasattr(other, "get_polygon"):
            polygon1 = CollisionPolygon(*self.get_polygon())
            polygon2 = CollisionPolygon(*other.get_polygon())
            return polygon1.is_collide(polygon2)
        raise TypeError(
            "No collision detection method found between "
            f"{self.__class__.__name__} and {other.__class__.__name__}"
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
    def __init__(self, x: number, y: number, radius: number) -> None:
        self._x = x
        self._y = y
        self._radius = radius

    def __contains__(self, point: Point2D) -> bool:
        point = self._inverse(point)
        center = (self._x, self._y)
        return math.dist(center, point) < self._radius

    def get_polygon(self) -> List[Point2D]:
        x0 = self._x
        y0 = self._y
        polygon = []
        for i in range(0, 360, 5):
            polygon.append(
                self._transform(
                    (
                        x0 + self._radius * math.cos(math.radians(i)),
                        y0 + self._radius * math.sin(math.radians(i)),
                    )
                )
            )
        return polygon

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
    def __init__(self, x: number, y: number, a: number, b: number) -> None:
        self._x = x
        self._y = y
        self._a = a
        self._b = b

    def __contains__(self, point: Point2D) -> bool:
        point = self._inverse(point)
        # Since directly testing whether a point is inside an ellipse is more
        # complicated, it is more convenient to transform it into a circle.
        point = (self._b / self._a * point[0], point[1])
        center = (self._b / self._a * self._x, self._y)
        return math.dist(center, point) < self._b

    def get_polygon(self) -> List[Point2D]:
        x0 = self._x
        y0 = self._y
        polygon = []
        for i in range(0, 360, 5):
            polygon.append(
                self._transform(
                    (
                        x0 + self._a * math.cos(math.radians(i)),
                        y0 + self._b * math.sin(math.radians(i)),
                    )
                )
            )
        return polygon

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
    def __init__(self, x: number, y: number, width: number, height: number):
        self._x = x
        self._y = y
        self._width = width
        self._height = height

    def __contains__(self, point: Point2D) -> bool:
        point = self._inverse(point)
        return self._x < point[0] < self._x + self._width and self._y < point[1] < self._y + self._height

    def get_polygon(self) -> List[Point2D]:
        return [
            self._transform(point)
            for point in [
                (self._x, self._y),
                (self._x + self._width, self._y),
                (self._x + self._width, self._y + self._height),
                (self._x, self._y + self._height),
            ]
        ]

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


class CollisionSector(CollisionShapeBase):
    def __init__(
        self,
        x: Point2D,
        y: Point2D,
        radius: number,
        angle: number,
        start_angle: number = 0,
    ) -> None:
        self._x = x
        self._y = y
        self._radius = radius
        self._angle = angle
        self._start_angle = start_angle

    def __contains__(self, point: Point2D) -> bool:
        point = self._inverse(point)
        center = (self._x, self._y)
        angle = math.atan2(point[1] - center[1], point[0] - center[0])
        if angle < 0:
            angle += 2 * math.pi
        angle = math.degrees(angle)
        if self._start_angle < angle < self._start_angle + self._angle:
            return math.dist(center, point) < self._radius
        return False

    @property
    def angle(self) -> number:
        """The angle of the sector, in degrees.

        :type: number
        """
        return self._angle

    @angle.setter
    def angle(self, value: number) -> None:
        self._angle = value

    @property
    def start_angle(self) -> number:
        """The start angle of the sector, in degrees.

        :type: number
        """
        return self._start_angle

    @start_angle.setter
    def start_angle(self, angle: number) -> None:
        self._start_angle = angle

    @property
    def radius(self) -> number:
        """The radius of the sector.

        :type: number
        """
        return self._radius

    @radius.setter
    def radius(self, value: number) -> None:
        self._radius = value


class CollisionPolygon(CollisionShapeBase):
    def __init__(self, *coordinates: Point2D) -> None:
        self._coordinates: List[Point2D] = list(coordinates)

    def __contains__(self, point: Point2D) -> bool:
        point = self._inverse(point)
        coords = self._coordinates + [self._coordinates[0]]
        return point_in_polygon(coords, point)

    def collide_with_CollisionPolygon(self, other: "CollisionPolygon") -> bool:
        return sat(self._coordinates, other._coordinates)

    def get_polygon(self) -> List[Point2D]:
        return [self._transform(point) for point in self._coordinates]

    @property
    def coordinates(self) -> List[Point2D]:
        """The coordinates for each point in the polygon.

        :type: List[Point2D]
        """
        return self._coordinates


__all__ = (
    "CollisionShapeBase",
    "CollisionCircle",
    "CollisionEllipse",
    "CollisionRectangle",
    "CollisionSector",
    "CollisionPolygon",
)
