"""Matrix and Vector math.

This module provides Vector and Matrix objects, including Vec2, Vec3,
Vec4, Mat3, and Mat4. Most common matrix and vector operations are
supported. Helper methods are included for rotating, scaling, and
transforming. The :py:class:`~pyglet.matrix.Mat4` includes class methods
for creating orthographic and perspective projection matrixes.

Matrices behave just like they do in GLSL: they are specified in column-major
order and multiply on the left of vectors, which are treated as columns.

All objects are immutable and hashable.
"""
# WARNING! DO NOT TRY TO MAKE THIS FILE "PRETTIER"
#
# The unusual code style in this module is an intentional sacrifice:
# * It allows decent performance despite being written in pure Python
# * It ensures good developer experience outside pyglet.math, especially
#   on systems without access to compute shaders
from __future__ import annotations

import math as _math
import typing as _typing
import warnings as _warnings


def clamp(num: float, minimum: float, maximum: float) -> float:
    """Clamp a value between a minimum and maximum limit."""
    return max(min(num, maximum), minimum)


class Vec2(_typing.NamedTuple):
    """A two-dimensional vector represented as an X Y coordinate pair.

    `Vec2` is an immutable 2D Vector, including most common
    operators. As an immutable type, all operations return a new object.

    .. note:: The Python ``len`` operator returns the number of elements in
              the vector. For the vector length, use the `length()` method.

    .. note:: Python's :py:func:`sum` requires the first item to be a ``Vec2``.

              After that, you can mix ``Vec2``-like :py:class:`tuple`
              and ``Vec2`` instances freely in the iterable.

              If you do not, you will see a :py:class:`TypeError` about being
              unable to add a :py:class:`tuple` and a :py:class:`int`.

    """

    x: float = 0.0
    y: float = 0.0

    def __bool__(self):
        return self.x != 0.0 or self.y != 0.0

    def __add__(self, other: Vec2 | tuple[float, float] | float) -> Vec2:
        try:
            return Vec2(
                self[0] + other[0], self[1] + other[1]  # type: ignore
            )
        except TypeError:
            return Vec2(
                self[0] + other, self[1] + other  # type: ignore
            )

    def __radd__(self, other: Vec2 | tuple[float, float] | float) -> Vec2:
        try:
            return self.__add__(other)
        except TypeError as err:
            if other == 0:  # Required for functionality with sum()
                return self
            raise err

    def __sub__(self, other: Vec2 | tuple[float, float] | float) -> Vec2:
        try:
            return Vec2(
                self[0] - other[0], self[1] - other[1]  # type: ignore
            )
        except TypeError:
            return Vec2(
                self[0] - other, self[1] - other  # type: ignore
            )

    def __rsub__(self, other: Vec2 | tuple[float, float] | float) -> Vec2:
        try:
            return Vec2(
                other[0] - self[0], other[1] - self[1]  # type: ignore
            )
        except TypeError:
            return Vec2(
                other - self[0], other - self[1]  # type: ignore
            )

    def __mul__(self, scalar: float | Vec2 | tuple[float, float]) -> Vec2:
        try:
            return Vec2(
                self[0] * scalar[0], self[1] * scalar[1]  # type: ignore
            )
        except TypeError:
            return Vec2(
                self[0] * scalar, self[1] * scalar  # type: ignore
            )

    def __rmul__(self, scalar: float | Vec2 | tuple[float, float]) -> Vec2:
        try:
            return Vec2(
                self[0] * scalar[0], self[1] * scalar[1]  # type: ignore
            )
        except TypeError:
            return Vec2(
                self[0] * scalar, self[1] * scalar  # type: ignore
            )

    def __truediv__(self, scalar: float | Vec2 | tuple[float, float]) -> Vec2:
        try:
            return Vec2(
                self[0] / scalar[0], self[1] / scalar[1]  # type: ignore
            )
        except TypeError:
            return Vec2(
                self[0] / scalar, self[1] / scalar  # type: ignore
            )

    def __rtruediv__(self, scalar: float | Vec2 | tuple[float, float]) -> Vec2:
        try:
            return Vec2(
                scalar[0] / self[0], scalar[1] / self[1]  # type: ignore
            )
        except TypeError:
            return Vec2(
                scalar / self[0], scalar / self[1]  # type: ignore
            )

    def __floordiv__(self, scalar: float | Vec2 | tuple[float, float]) -> Vec2:
        try:
            return Vec2(
                self.x // scalar[0], self.y // scalar[1]  # type: ignore
            )
        except TypeError:
            return Vec2(
                self[0] // scalar, self[1] // scalar  # type: ignore
            )

    def __rfloordiv__(self, scalar: float | Vec2 | tuple[float, float]) -> Vec2:
        try:
            return Vec2(
                scalar[0] // self[0], scalar[1] // self[1]  # type: ignore
            )
        except TypeError:
            return Vec2(
                scalar // self[0], scalar // self[1]  # type: ignore
            )

    def __abs__(self) -> Vec2:
        return Vec2(abs(self[0]), abs(self[1]))

    def __neg__(self) -> Vec2:
        return Vec2(-self[0], -self[1])

    def __round__(self, n_digits: int | None = None) -> Vec2:
        return Vec2(*(round(v, n_digits) for v in self))

    def __ceil__(self) -> Vec2:
        return Vec2(_math.ceil(self[0]), _math.ceil(self[1]))

    def __floor__(self) -> Vec2:
        return Vec2(_math.floor(self[0]), _math.floor(self[1]))

    def __trunc__(self) -> Vec2:
        return Vec2(_math.trunc(self[0]), _math.trunc(self[1]))

    def __mod__(self, other: Vec2 | tuple[float, float] | float) -> Vec2:
        try:
            return Vec2(
                self[0] % other[0], self[1] % other[1]  # type: ignore
            )
        except TypeError:
            return Vec2(
                self[0] % other, self[1] % other  # type: ignore
            )

    def __pow__(self, other: Vec2 | tuple[float, float] | float) -> Vec2:
        try:
            return Vec2(
                self[0] ** other[0], self[1] ** other[1]  # type: ignore
            )
        except TypeError:
            return Vec2(
                self[0] ** other, self[1] ** other  # type: ignore
            )

    def __lt__(self, other: tuple[float, float]) -> bool:
        return self[0] ** 2 + self[0] ** 2 < other[0] ** 2 + other[1] ** 2

    @staticmethod
    def from_heading(heading: float, length: float = 1.0) -> Vec2:
        """Create a new vector from the given heading and length.

        Args:
          heading: The desired heading, in radians
          length: The desired length of the vector
        """
        return Vec2(length * _math.cos(heading), length * _math.sin(heading))

    @staticmethod
    def from_polar(angle: float, length: float = 1.0) -> Vec2:
        """Create a new vector from the given polar coordinates.

        Args:
          angle: The angle, in radians.
          length: The desired length
        """
        return Vec2(length * _math.cos(angle), length * _math.sin(angle))

    def length(self) -> float:
        """Calculate the length of the vector: ``sqrt(x ** 2 + y ** 2)``."""
        return _math.sqrt(self[0] ** 2 + self[1] ** 2)

    def heading(self) -> float:
        """Calculate the heading of the vector in radians.

        Shortcut for `atan2(y, x)` meaning it returns a value between
        -pi and pi. ``Vec2(1, 0)`` will have a heading of 0. Counter-clockwise
        is positive moving towards pi, and clockwise is negative moving towards -pi.
        """
        return _math.atan2(self[1], self[0])

    def length_squared(self) -> float:
        """Calculate the squared length of the vector.

        This is simply shortcut for `x ** 2 + y ** 2` and can be used
        for faster comparisons without the need for a square root.
        """
        return self[0] ** 2.0 + self[1] ** 2.0

    def lerp(self, other: Vec2 | tuple[float, float], amount: float) -> Vec2:
        """Create a new Vec2 linearly interpolated between this vector and another Vec2.

        The equivalent in GLSL is `mix`.

        Args:
          other: Another Vec2 instance.
          amount: The amount of interpolation between this vector, and the other
                  vector. This should be a value between 0.0 and 1.0. For example:
                  0.5 is the midway point between both vectors.
        """
        return Vec2(self[0] + (amount * (other[0] - self.x)), self[1] + (amount * (other[1] - self[1])))

    def step(self, edge: Vec2 | tuple[float, float]) -> Vec2:
        """A step function that returns 0.0 for a component if it is less than the edge, and 1.0 otherwise.

        This can be used enable and disable some behavior based on a condition.

        Example::

            # First component is less than 1.0, second component is greater than 1.0
            Vec2(0.5, 1.5).step((1.0, 1.0))
            Vec2(1.0, 0.0)

        Args:
            edge: A Vec2 instance.
        """
        return Vec2(0.0 if self[0] < edge[0] else 1.0, 0.0 if self[1] < edge[1] else 1.0)

    def reflect(self, vector: Vec2 | tuple[float, float]) -> Vec2:
        """Create a new Vec2 reflected (ricochet) from the given normalized vector.

        Args:
            vector: A normalized Vec2 or Vec2-like tuple.
        """
        # Less unrolled equivalent of code below:
        #  return self - vector * 2 * vector.dot(self)
        twice_dot_value = self.dot(vector) * 2
        return Vec2(
            self[0] - twice_dot_value * vector[0],
            self[1] - twice_dot_value * vector[1]
        )

    def rotate(self, angle: float) -> Vec2:
        """Create a new vector rotated by the angle. The length remains unchanged.

        Args:
            angle: The desired angle, in radians.
        """
        s = _math.sin(angle)
        c = _math.cos(angle)
        return Vec2(c * self[0] - s * self[1], s * self[0] + c * self[1])

    def distance(self, other: Vec2 | tuple[int, int]) -> float:
        """Calculate the distance between this vector and another vector.

        Args:
            other: The point to calculate the distance to.
        """
        return _math.sqrt(((other[0] - self[0]) ** 2) + ((other[1] - self[1]) ** 2))

    def normalize(self) -> Vec2:
        """Return a normalized version of the vector.

        This simply means the vector will have a length of 1.0. If the vector
        has a length of 0, the original vector will be returned.
        """
        d = _math.sqrt(self[0] ** 2 + self[1] ** 2)
        if d:
            return Vec2(self[0] / d, self[1] / d)
        return self

    if _typing.TYPE_CHECKING:
        @_typing.overload
        def clamp(self, min_val: float, max_val: float) -> Vec2:
            ...

        @_typing.overload
        def clamp(self, min_val: Vec2 | tuple[float, float], max_val: Vec2 | tuple[float, float]) -> Vec2:
            ...

        # -- Begin revert if perf-impacting block --
        @_typing.overload
        def clamp(self, min_val: Vec2 | tuple[float, float], max_val: float) -> Vec2:
            ...

        @_typing.overload
        def clamp(self, min_val: float, max_val: Vec2 | tuple[float, float]) -> Vec2:
            ...
        # -- End revert if perf-impacting block --

    def clamp(self, min_val: Vec2 | tuple[float, float] | float, max_val: Vec2 | tuple[float, float] | float) -> Vec2:
        """Restrict the value of the X and Y components of the vector to be within the given values.

        If a single value is provided, it will be used for both X and Y.
        If a tuple or Vec2 is provided, the first value will be used for X and the second for Y.

        Args:
            min_val: The minimum value(s)
            max_val: The maximum value(s)
        """
        try:
            min_x, min_y = min_val[0], min_val[1]  # type: ignore
        except TypeError:
            min_x = min_val
            min_y = min_val
        try:
            max_x, max_y = max_val[0], max_val[1]  # type: ignore
        except TypeError:
            max_x = max_val
            max_y = max_val

        return Vec2(
            clamp(self[0], min_x, max_x), clamp(self[1], min_y, max_y),  # type: ignore
        )

    def dot(self, other: Vec2 | tuple[float, float]) -> float:
        """Calculate the dot product of this vector and another 2D vector."""
        return self[0] * other[0] + self[1] * other[1]

    def index(self, *args: _typing.Any) -> int:
        raise NotImplementedError("Vec types can be indexed directly.")

    def __getattr__(self, attrs: str) -> Vec2 | Vec3 | Vec4:
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}[len(attrs)]
            return vec_class(*(self['xy'.index(c)] for c in attrs))
        except (ValueError, KeyError, TypeError) as err:
            msg = f"'Vec2' has no attribute: '{attrs}'."
            raise AttributeError(msg) from err


class Vec3(_typing.NamedTuple):
    """A three-dimensional vector represented as X Y Z coordinates.

    `Vec3` is an immutable 3D Vector, including most common operators.
    As an immutable type, all operations return a new object.

    .. note:: The Python ``len`` operator returns the number of elements in
              the vector. For the vector length, use the `length()` method.
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __bool__(self):
        return self.x != 0.0 or self.y != 0.0 or self.z != 0.0

    def __add__(self, other: Vec3 | tuple[float, float, float] | float) -> Vec3:
        try:
            return Vec3(
                self[0] + other[0], self[1] + other[1], self[2] + other[2]  # type: ignore
            )
        except TypeError:
            return Vec3(
                self[0] + other, self[1] + other, self[2] + other  # type: ignore
            )

    def __radd__(self, other: Vec3 | tuple[float, float, float] | float) -> Vec3:
        try:
            return self.__add__(_typing.cast(Vec3, other))
        except TypeError as err:
            if other == 0:  # Required for functionality with sum()
                return self
            raise err

    def __sub__(self, other: Vec3 | tuple[float, float, float] | float) -> Vec3:
        try:
            return Vec3(
                self[0] - other[0], self[1] - other[1], self[2] - other[2]  # type: ignore
            )
        except TypeError:
            return Vec3(
                self[0] - other, self[1] - other, self[2] - other  # type: ignore
            )

    def __rsub__(self, other: Vec3 | tuple[float, float, float] | float) -> Vec3:
        try:
            return Vec3(
                other[0] - self[0], other[1] - self[1], other[2] - self[2]  # type: ignore
            )
        except TypeError:
            return Vec3(
                other - self[0], other - self[1], other - self[2]  # type: ignore
            )

    def __mul__(self, scalar: float | Vec3 | tuple[float, float, float]) -> Vec3:
        try:
            return Vec3(
                self[0] * scalar[0], self[1] * scalar[1], self[2] * scalar[2]  # type: ignore
            )
        except TypeError:
            return Vec3(
                self[0] * scalar, self[1] * scalar, self[2] * scalar  # type: ignore
            )

    def __rmul__(self, scalar: float | Vec3 | tuple[float, float, float]) -> Vec3:
        try:
            return Vec3(
                self[0] * scalar[0], self[1] * scalar[1], self[2] * scalar[2]  # type: ignore
            )
        except TypeError:
            return Vec3(
                self[0] * scalar, self[1] * scalar, self[2] * scalar  # type: ignore
            )

    def __truediv__(self, scalar: float | Vec3 | tuple[float, float, float]) -> Vec3:
        try:
            return Vec3(
                self[0] / scalar[0], self[1] / scalar[1], self[2] / scalar[2]  # type: ignore
            )
        except TypeError:
            return Vec3(
                self[0] / scalar, self[1] / scalar, self[2] / scalar  # type: ignore
            )

    def __rtruediv__(self, other: float | Vec3 | tuple[float, float, float]) -> Vec3:
        try:
            return Vec3(
                other[0] / self[0], other[1] / self[1], other[2] / self[2]  # type: ignore
            )
        except TypeError:
            return Vec3(
                other / self[0], other / self[1], other / self[2]  # type: ignore
            )

    def __floordiv__(self, other: float | Vec3 | tuple[float, float, float]) -> Vec3:
        try:
            return Vec3(
                self[0] // other[0], self[1] // other[1], self[2] // other[2]  # type: ignore
            )
        except TypeError:
            return Vec3(
                self[0] // other, self[1] // other, self[2] // other  # type: ignore
            )

    def __rfloordiv__(self, other: float | Vec3 | tuple[float, float, float]) -> Vec3:
        try:
            return Vec3(
                other[0] // self[0], other[1] // self[1], other[2] // self[2]  # type: ignore
            )
        except TypeError:
            return Vec3(
                other // self[0], other // self[1], other // self[2]  # type: ignore
            )

    def __abs__(self) -> Vec3:
        return Vec3(abs(self[0]), abs(self[1]), abs(self[2]))

    def __neg__(self) -> Vec3:
        return Vec3(-self[0], -self[1], -self[2])

    def __round__(self, n_digits: int | None = None) -> Vec3:
        return Vec3(*(round(v, n_digits) for v in self))

    def __ceil__(self) -> Vec3:
        return Vec3(_math.ceil(self[0]), _math.ceil(self[1]), _math.ceil(self[2]))

    def __floor__(self) -> Vec3:
        return Vec3(_math.floor(self[0]), _math.floor(self[1]), _math.floor(self[2]))

    def __trunc__(self) -> Vec3:
        return Vec3(_math.trunc(self[0]), _math.trunc(self[1]), _math.trunc(self[2]))

    def __mod__(self, other: Vec3 | tuple[float, float, float] | float) -> Vec3:
        try:
            return Vec3(
                self[0] % other[0], self[1] % other[1], self[2] % other[2]  # type: ignore
            )
        except TypeError:
            return Vec3(
                self[0] % other, self[1] % other, self[2] % other  # type: ignore
            )

    def __pow__(self, other: Vec3 | tuple[float, float, float] | float) -> Vec3:
        try:
            return Vec3(
                self[0] ** other[0], self[1] ** other[1], self[2] ** other[2]  # type: ignore
            )
        except TypeError:
            return Vec3(
                self[0] ** other, self[1] ** other, self[2] ** other  # type: ignore
            )

    def __lt__(self, other: Vec3 | tuple[float, float, float]) -> bool:
        return self[0] ** 2 + self[1] ** 2 + self[2] ** 2 < other[0] ** 2 + other[1] ** 2 + other[2] ** 2

    @classmethod
    def from_pitch_yaw(cls, pitch: float, yaw: float) -> Vec3:
        """Create a unit vector from pitch and yaw in radians.

        Args:
            pitch: The pitch value in radians
            yaw: The yaw value in radians
        """
        return Vec3(
            _math.cos(yaw) * _math.cos(pitch),
            _math.sin(pitch),
            _math.sin(yaw) * _math.cos(pitch),
        ).normalize()

    def get_pitch_yaw(self) -> tuple[float, float]:
        """Get the pitch and yaw angles from a unit vector in radians."""
        return _math.asin(self.y), _math.atan2(self.z, self.x)

    def length(self) -> float:
        """Calculate the length of the vector: ``sqrt(x ** 2 + y ** 2 + z ** 2)``."""
        return _math.sqrt(self[0] ** 2 + self[1] ** 2 + self[2] ** 2)

    def length_squared(self) -> float:
        """Calculate the squared length of the vector.

        This is simply shortcut for `x ** 2 + y ** 2 + z ** 2` and can be used
        for faster comparisons without the need for a square root.
        """
        return self[0] ** 2 + self[1] ** 2 + self[2] ** 2

    def cross(self, other: Vec3 | tuple[float, float, float]) -> Vec3:
        """Calculate the cross product of this vector and another 3D vector.

        Args:
            other: Another Vec3 or tuple of 3 floats.
        """
        return Vec3(
            (self.y * other[2]) - (self.z * other[1]),
            (self.z * other[0]) - (self.x * other[2]),
            (self.x * other[1]) - (self.y * other[0]),
        )

    def dot(self, other: Vec3 | tuple[float, float, float]) -> float:
        """Calculate the dot product of this vector and another 3D vector.

        Args:
            other: Another Vec3 or tuple of 3 floats.
        """
        return self.x * other[0] + self.y * other[1] + self.z * other[2]

    def lerp(self, other: Vec3 | tuple[float, float, float], alpha: float) -> Vec3:
        """Create a new Vec3 linearly interpolated between this vector and another Vec3-like.

        Args:
          other: Another Vec3 instance or tuple of 3 floats.
          alpha: The amount of interpolation between this vector, and the other
                 vector. This should be a value between 0.0 and 1.0. For example:
                 0.5 is the midway point between both vectors.
        """
        return Vec3(
            self.x + (alpha * (other[0] - self.x)),
            self.y + (alpha * (other[1] - self.y)),
            self.z + (alpha * (other[2] - self.z)),
        )

    def distance(self, other: Vec3 | tuple[float, float, float]) -> float:
        """Calculate the distance between this vector and another 3D vector.

        Args:
            other: The point to calculate the distance to.
        """
        return _math.sqrt(((other[0] - self.x) ** 2) + ((other[1] - self.y) ** 2) + ((other[2] - self.z) ** 2))

    def normalize(self) -> Vec3:
        """Return a normalized version of the vector.

        This simply means the vector will have a length of 1.0. If the vector
        has a length of 0, the original vector will be returned.
        """
        try:
            d = _math.sqrt(self[0] ** 2 + self[1] ** 2 + self[2] ** 2)
            return Vec3(self.x / d, self.y / d, self.z / d)
        except ZeroDivisionError:
            return self

    if _typing.TYPE_CHECKING:
        @_typing.overload
        def clamp(self, min_val: float, max_val: float) -> Vec3:
            ...

        @_typing.overload
        def clamp(self, min_val: Vec3 | tuple[float, float, float], max_val: Vec3 | tuple[float, float, float]) -> Vec3:
            ...

        # -- Begin revert if perf-impacting block --
        @_typing.overload
        def clamp(self, min_val: Vec3 | tuple[float, float, float], max_val: float) -> Vec3:
            ...

        @_typing.overload
        def clamp(self, min_val: float, max_val: Vec3 | tuple[float, float, float]) -> Vec3:
            ...
        # -- End revert if perf-impacting block --

    def clamp(self, min_val: float | Vec3 | tuple[float, float, float],
              max_val: float | Vec3 | tuple[float, float, float]) -> Vec3:
        """Restrict the value of the X, Y and Z components of the vector to be within the given values.

        If a single value is provided, it will be used for all components.
        If a tuple or Vec3 is provided, the first value will be used for X, the second for Y, and the third for Z.

        Args:
            min_val: The minimum value(s)
            max_val: The maximum value(s)
        """
        try:
            min_x, min_y, min_z = min_val[0], min_val[1], min_val[2]  # type: ignore
        except TypeError:
            min_x = min_val
            min_y = min_val
            min_z = min_val
        try:
            max_x, max_y, max_z = max_val[0], max_val[1], max_val[2]  # type: ignore
        except TypeError:
            max_x = max_val
            max_y = max_val
            max_z = max_val

        return Vec3(
            clamp(self[0], min_x, max_x), clamp(self[1], min_y, max_y), clamp(self[2], min_z, max_z)  # type: ignore
        )

    def index(self, *args: _typing.Any) -> int:
        raise NotImplementedError("Vec types can be indexed directly.")

    def __getattr__(self, attrs: str) -> Vec2 | Vec3 | Vec4:
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}[len(attrs)]
            return vec_class(*(self['xyz'.index(c)] for c in attrs))
        except (ValueError, KeyError, TypeError) as err:
            msg = f"'Vec3' has no attribute: '{attrs}'."
            raise AttributeError(msg) from err


class Vec4(_typing.NamedTuple):
    """A four-dimensional vector represented as X Y Z W coordinates.

    `Vec4` is an immutable 4D Vector, including most common operators.
    As an immutable type, all operations return a new object.

    .. note:: The Python ``len` operator returns the number of elements in
              the vector. For the vector length, use the `length()` method.
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 0.0

    def __bool__(self):
        return self.x != 0.0 or self.y != 0.0 or self.z != 0.0 or self.w != 0.0

    def __add__(self, other: Vec4 | tuple[float, float, float, float] | float) -> Vec4:
        try:
            return Vec4(
                other[0] + self[0], other[1] + self[1], other[2] + self[2], other[3] + self[3]  # type: ignore
            )
        except TypeError:
            return Vec4(
                other + self[0], other + self[1], other + self[2], other + self[3]  # type: ignore
            )

    def __radd__(self, other: Vec4 | tuple[float, float, float, float] | int) -> Vec4:
        try:
            return self.__add__(_typing.cast(Vec4, other))
        except TypeError as err:
            if other == 0:  # Required for functionality with sum()
                return self
            raise err

    def __sub__(self, other: Vec4 | tuple[float, float, float, float] | float) -> Vec4:
        try:
            return Vec4(
                self[0] - other[0], self[1] - other[1], self[2] - other[2], self[3] - other[3]  # type: ignore
            )
        except TypeError:
            return Vec4(
                self[0] - other, self[1] - other, self[2] - other, self[3] - other  # type: ignore
            )

    def __rsub__(self, other: Vec4 | tuple[float, float, float, float] | float) -> Vec4:
        try:
            return Vec4(
                other[0] - self[0], other[1] - self[1], other[2] - self[2], other[3] - self[3]  # type: ignore
            )
        except TypeError:
            return Vec4(
                other - self[0], other - self[1], other - self[2], other - self[3]  # type: ignore
            )

    def __mul__(self, scalar: float | Vec4 | tuple[float, float, float, float]) -> Vec4:
        try:
            return Vec4(
                self[0] * scalar[0], self[1] * scalar[1], self[2] * scalar[2], self[3] * scalar[3]  # type: ignore
            )
        except TypeError:
            return Vec4(
                self[0] * scalar, self[1] * scalar, self[2] * scalar, self[3] * scalar  # type: ignore
            )

    def __rmul__(self, scalar: float | Vec4 | tuple[float, float, float, float]) -> Vec4:
        try:
            return Vec4(
                self[0] * scalar[0], self[1] * scalar[1], self[2] * scalar[2], self[3] * scalar[3]  # type: ignore
            )
        except TypeError:
            return Vec4(
                self[0] * scalar, self[1] * scalar, self[2] * scalar, self[3] * scalar  # type: ignore
            )

    def __truediv__(self, scalar: float | Vec4 | tuple[float, float, float, float]) -> Vec4:
        try:
            return Vec4(
                self[0] / scalar[0], self[1] / scalar[1], self[2] / scalar[2], self[3] / scalar[3]  # type: ignore
            )
        except TypeError:
            return Vec4(
                self[0] / scalar, self[1] / scalar, self[2] / scalar, self[3] / scalar  # type: ignore
            )

    def __rtruediv__(self, scalar: float | Vec4 | tuple[float, float, float, float]) -> Vec4:
        try:
            return Vec4(
                scalar[0] / self[0], scalar[1] / self[1], scalar[2] / self[2], scalar[3] / self[3]  # type: ignore
            )
        except TypeError:
            return Vec4(
                scalar / self[0], scalar / self[1], scalar / self[2], scalar / self[3]  # type: ignore
            )

    def __floordiv__(self, scalar: float | Vec4 | tuple[float, float, float, float]) -> Vec4:
        try:
            return Vec4(
                self[0] // scalar[0], self[1] // scalar[1], self[2] // scalar[2], self[3] // scalar[3]  # type: ignore
            )
        except TypeError:
            return Vec4(
                self[0] // scalar, self[1] // scalar, self[2] // scalar, self[3] // scalar  # type: ignore
            )

    def __rfloordiv__(self, scalar: float | Vec4 | tuple[float, float, float, float]) -> Vec4:
        try:
            return Vec4(
                scalar[0] // self[0], scalar[1] // self[1], scalar[2] // self[2], scalar[3] // self[3]  # type: ignore
            )
        except TypeError:
            return Vec4(
                scalar // self[0], scalar // self[1], scalar // self[2], scalar // self[3]  # type: ignore
            )

    def __abs__(self) -> Vec4:
        return Vec4(abs(self[0]), abs(self[1]), abs(self[2]), abs(self[3]))

    def __neg__(self) -> Vec4:
        return Vec4(-self.x, -self.y, -self.z, -self.w)

    def __round__(self, n_digits: int | None = None) -> Vec4:
        return Vec4(*(round(v, n_digits) for v in self))

    def __ceil__(self) -> Vec4:
        return Vec4(_math.ceil(self[0]), _math.ceil(self[1]), _math.ceil(self[2]), _math.ceil(self[3]))

    def __floor__(self) -> Vec4:
        return Vec4(_math.floor(self[0]), _math.floor(self[1]), _math.floor(self[2]), _math.floor(self[3]))

    def __trunc__(self) -> Vec4:
        return Vec4(_math.trunc(self[0]), _math.trunc(self[1]), _math.trunc(self[2]), _math.trunc(self[3]))

    def __mod__(self, other: Vec4 | tuple[int, int, int, int] | float) -> Vec4:
        try:
            return Vec4(
                self[0] % other[0], self[1] % other[1], self[2] % other[2], self[3] % other[3]  # type: ignore
            )
        except TypeError:
            return Vec4(
                self[0] % other, self[1] % other, self[2] % other, self[3] % other  # type: ignore
            )

    def __pow__(self, other: Vec4 | tuple[int, int, int, int] | float) -> Vec4:
        try:
            return Vec4(
                self[0] ** other[0], self[1] ** other[1], self[2] ** other[2], self[3] ** other[3]  # type: ignore
            )
        except TypeError:
            return Vec4(
                self[0] ** other, self[1] ** other, self[2] ** other, self[3] ** other  # type: ignore
            )

    def __lt__(self, other: Vec4 | tuple[float, float, float, float]) -> bool:
        return self[0] ** 2 + self[1] ** 2 + self[2] ** 2 < other[0] ** 2 + other[1] ** 2 + other[2] ** 2

    def length(self) -> float:
        """Calculate the length of the vector: ``sqrt(x ** 2 + y ** 2 + z ** 2 + w ** 2)``."""
        return _math.sqrt(self[0] ** 2 + self[1] ** 2 + self[2] ** 2 + self[3] ** 2)

    def length_squared(self) -> float:
        """Calculate the squared length of the vector.

        This is simply shortcut for `x ** 2 + y ** 2 + z ** 2 + w ** 2` and can be used
        for faster comparisons without the need for a square root.
        """
        return self[0] ** 2 + self[1] ** 2 + self[2] ** 2 + self[3] ** 2

    def lerp(self, other: Vec4 | tuple[float, float, float, float], amount: float) -> Vec4:
        """Create a new Vec4 linearly interpolated between this vector and another Vec4.

        Args:
          other: Another Vec4 instance.
          amount: The amount of interpolation between this vector, and the other
                  vector. This should be a value between 0.0 and 1.0. For example:
                  0.5 is the midway point between both vectors.
        """
        return Vec4(
            self.x + (amount * (other.x - self.x)),
            self.y + (amount * (other.y - self.y)),
            self.z + (amount * (other.z - self.z)),
            self.w + (amount * (other.w - self.w)),
        )

    def distance(self, other: Vec4 | tuple[float, float, float, float]) -> float:
        """Calculate the distance between this vector and another 4D vector.

        Args:
            other: The point to calculate the distance to.
        """
        return _math.sqrt(
            ((other.x - self.x) ** 2)
            + ((other.y - self.y) ** 2)
            + ((other.z - self.z) ** 2)
            + ((other.w - self.w) ** 2),
        )

    def normalize(self) -> Vec4:
        """Returns a normalized version of the vector meaning a version that has length 1.

        This means that the vector will have the same direction, but a length of 1.0.
        If the vector has a length of 0, the original vector will be returned.
        """
        d = _math.sqrt(self[0] ** 2 + self[1] ** 2 + self[2] ** 2 + self[3] ** 2)
        if d:
            return Vec4(self[0] / d, self[1] / d, self[2] / d, self[3] / d)
        return self

    if _typing.TYPE_CHECKING:
        @_typing.overload
        def clamp(self, min_val: float, max_val: float) -> Vec4:
            ...

        @_typing.overload
        def clamp(self, min_val: tuple[float, float, float, float], max_val: tuple[float, float, float, float]) -> Vec4:
            ...

        # -- Begin revert if perf-impacting block --
        @_typing.overload
        def clamp(self, min_val: tuple[float, float, float, float], max_val: float) -> Vec4:
            ...

        @_typing.overload
        def clamp(self, min_val: float, max_val: tuple[float, float, float, float]) -> Vec4:
            ...
        # -- End revert if perf-impacting block --

    def clamp(
        self,
        min_val: float | tuple[float, float, float, float],
        max_val: float | tuple[float, float, float, float],
    ) -> Vec4:
        """Restrict the value of the X, Y, Z and W components of the vector to be within the given values.

        The minimum and maximum values can be a single value that will be applied to all components,
        or a tuple of 4 values that will be applied to each component respectively.

        Args:
            min_val: The minimum value(s)
            max_val: The maximum value(s)
        """
        try:
            min_x, min_y, min_z, min_w = min_val[0], min_val[1], min_val[2], min_val[3]  # type: ignore
        except TypeError:
            min_x = min_val
            min_y = min_val
            min_z = min_val
            min_w = min_val
        try:
            max_x, max_y, max_z, max_w = max_val[0], max_val[1],  max_val[2], max_val[3]  # type: ignore
        except TypeError:
            max_x = max_val
            max_y = max_val
            max_z = max_val
            max_w = max_val

        return Vec4(
            clamp(self[0], min_x, max_x), clamp(self[1], min_y, max_y),  # type: ignore
            clamp(self[2], min_z, max_z), clamp(self[3], min_w, max_w),  # type: ignore
        )

    def dot(self, other: Vec4 | tuple[float, float, float, float]) -> float:
        """Calculate the dot product of this vector and another 4D vector.

        Args:
            other: Another Vec4 instance.
        """
        return self.x * other.x + self.y * other.y + self.z * other.z + self.w * other.w

    def index(self, *args: _typing.Any) -> int:
        raise NotImplementedError("Vec types can be indexed directly.")

    def __getattr__(self, attrs: str) -> Vec2 | Vec3 | Vec4:
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}[len(attrs)]
            return vec_class(*(self['xyzw'.index(c)] for c in attrs))
        except (ValueError, KeyError, TypeError) as err:
            msg = f"'Vec4' has no attribute: '{attrs}'."
            raise AttributeError(msg) from err


class Mat3(_typing.NamedTuple):
    """A 3x3 Matrix.

    `Mat3` is an immutable 3x3 Matrix, which includes most common operators.

    A Matrix can be created with a list or tuple of 9 values.
    If no values are provided, an "identity matrix" will be created
    (1.0 on the main diagonal). Because Mat3 objects are immutable,
    all operations return a new Mat3 object.

    .. note:: Matrix multiplication is performed using the "@" operator.
    """

    a: float = 1.0
    b: float = 0.0
    c: float = 0.0

    d: float = 0.0
    e: float = 1.0
    f: float = 0.0

    g: float = 0.0
    h: float = 0.0
    i: float = 1.0

    def scale(self, sx: float, sy: float) -> Mat3:
        return self @ Mat3(1.0 / sx, 0.0, 0.0, 0.0, 1.0 / sy, 0.0, 0.0, 0.0, 1.0)

    def translate(self, tx: float, ty: float) -> Mat3:
        return self @ Mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, -tx, ty, 1.0)

    def rotate(self, phi: float) -> Mat3:
        s = _math.sin(_math.radians(phi))
        c = _math.cos(_math.radians(phi))
        return self @ Mat3(c, s, 0.0, -s, c, 0.0, 0.0, 0.0, 1.0)

    def shear(self, sx: float, sy: float) -> Mat3:
        return self @ Mat3(1.0, sy, 0.0, sx, 1.0, 0.0, 0.0, 0.0, 1.0)

    def __add__(self, other: Mat3) -> Mat3:
        if not isinstance(other, Mat3):
            raise TypeError("Can only add to other Mat3 types")
        return Mat3(*(s + o for s, o in zip(self, other)))

    def __sub__(self, other: Mat3) -> Mat3:
        if not isinstance(other, Mat3):
            raise TypeError("Can only subtract from other Mat3 types")
        return Mat3(*(s - o for s, o in zip(self, other)))

    def __pos__(self) -> Mat3:
        return self

    def __neg__(self) -> Mat3:
        return Mat3(*(-v for v in self))

    def __invert__(self) -> Mat3:
        # extract the elements in row-column form. (matrix is stored column first)
        a11, a12, a13, a21, a22, a23, a31, a32, a33 = self

        # Calculate Adj(self) values column-row order
        # | a d g |
        # | b e h |
        # | c f i |
        a = a22 * a33 - a32 * a23  # +
        b = a31 * a23 - a21 * a33  # -
        c = a21 * a32 - a22 * a31  # +
        d = a32 * a13 - a12 * a33  # -
        e = a11 * a33 - a31 * a13  # +
        f = a31 * a12 - a11 * a32  # -
        g = a12 * a23 - a22 * a13  # +
        h = a21 * a13 - a11 * a23  # -
        i = a11 * a22 - a21 * a12  # +

        # Calculate determinant
        det = a11 * a + a21 * d + a31 * g

        if det == 0:
            _warnings.warn("Unable to calculate inverse of singular Matrix")
            return self

        # get determinant reciprocal
        rep = 1.0 / det

        # get inverse: A^-1 = def(A)^-1 * adj(A)
        return Mat3(*(a * rep, b * rep, c * rep,
                      d * rep, e * rep, f * rep,
                      g * rep, h * rep, i * rep))

    def __round__(self, ndigits: int | None = None) -> Mat3:
        return Mat3(*(round(v, ndigits) for v in self))

    def __mul__(self, other: object) -> _typing.NoReturn:
        msg = "Please use the @ operator for Matrix multiplication."
        raise NotImplementedError(msg)

    @_typing.overload
    def __matmul__(self, other: Vec3) -> Vec3: ...

    @_typing.overload
    def __matmul__(self, other: Mat3) -> Mat3: ...

    def __matmul__(self, other) -> Vec3 | Mat3:
        if isinstance(other, Vec3):
            x, y, z = other
            # extract the elements in row-column form. (matrix is stored column first)
            a11, a12, a13, a21, a22, a23, a31, a32, a33 = self
            return Vec3(
                a11 * x + a21 * y + a31 * z,
                a12 * x + a22 * y + a32 * z,
                a13 * x + a23 * y + a33 * z,
            )

        if not isinstance(other, Mat3):
            msg = "Can only multiply with Mat3 or Vec3 types"
            raise TypeError(msg)

        # extract the elements in row-column form. (matrix is stored column first)
        a11, a12, a13, a21, a22, a23, a31, a32, a33 = self
        b11, b12, b13, b21, b22, b23, b31, b32, b33 = other

        # Multiply and sum rows * columns
        return Mat3(
            # Column 1
            a11 * b11 + a21 * b12 + a31 * b13, a12 * b11 + a22 * b12 + a32 * b13, a13 * b11 + a23 * b12 + a33 * b13,
            # Column 2
            a11 * b21 + a21 * b22 + a31 * b23, a12 * b21 + a22 * b22 + a32 * b23, a13 * b21 + a23 * b22 + a33 * b23,
            # Column 3
            a11 * b31 + a21 * b32 + a31 * b33, a12 * b31 + a22 * b32 + a32 * b33, a13 * b31 + a23 * b32 + a33 * b33,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self[0:3]}\n    {self[3:6]}\n    {self[6:9]}"


class Mat4(_typing.NamedTuple):
    """A 4x4 Matrix.

    ``Mat4`` is an immutable 4x4 Matrix object with most common operators.
    This includes class methods for creating orthogonal and perspective
    projection matrixes, which can be used directly by OpenGL.

    You can create a Matrix with 16 initial values (floats), or no values
    at all. If no values are provided, an "identity matrix" will be created
    (1.0 on the main diagonal). ``Mat4`` objects are immutable, so all
    operations will return a new Mat4 object.

    Note:
        Matrix multiplication is performed using the "@" operator.
    """

    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 0.0

    e: float = 0.0
    f: float = 1.0
    g: float = 0.0
    h: float = 0.0

    i: float = 0.0
    j: float = 0.0
    k: float = 1.0
    l: float = 0.0

    m: float = 0.0
    n: float = 0.0
    o: float = 0.0
    p: float = 1.0

    @classmethod
    def orthogonal_projection(cls: type[Mat4], left: float, right: float, bottom: float, top: float,
                              z_near: float, z_far: float) -> Mat4:
        """Create a Mat4 orthographic projection matrix for use with OpenGL.

        Given left, right, bottom, top values, and near/far z planes,
        create a 4x4 Projection Matrix. This is useful for setting
        :py:attr:`~pyglet.window.Window.projection`.
        """
        width = right - left
        height = top - bottom
        depth = z_far - z_near

        s_x = 2.0 / width
        s_y = 2.0 / height
        s_z = 2.0 / -depth

        t_x = -(right + left) / width
        t_y = -(top + bottom) / height
        t_z = -(z_far + z_near) / depth

        return cls(s_x, 0.0, 0.0, 0.0,
                   0.0, s_y, 0.0, 0.0,
                   0.0, 0.0, s_z, 0.0,
                   t_x, t_y, t_z, 1.0)

    @classmethod
    def perspective_projection(cls: type[Mat4], aspect: float, z_near: float, z_far: float, fov: float = 60) -> Mat4:
        """Create a Mat4 perspective projection matrix for use with OpenGL.

        Given a desired aspect ratio, near/far planes, and fov (field of view),
        create a 4x4 Projection Matrix. This is useful for setting
        :py:attr:`~pyglet.window.Window.projection`.
        """
        xy_max = z_near * _math.tan(fov * _math.pi / 360)
        y_min = -xy_max
        x_min = -xy_max

        width = xy_max - x_min
        height = xy_max - y_min
        depth = z_far - z_near
        q = -(z_far + z_near) / depth
        qn = -2 * z_far * z_near / depth

        w = 2 * z_near / width
        w = w / aspect
        h = 2 * z_near / height

        return cls(w, 0, 0, 0,
                   0, h, 0, 0,
                   0, 0, q, -1,
                   0, 0, qn, 0)

    @classmethod
    def from_rotation(cls, angle: float, vector: Vec3) -> Mat4:
        """Create a rotation matrix from an angle and Vec3.

        Args:
          angle: The desired angle, in radians.
          vector: A Vec3 indicating the direction.
        """
        return cls().rotate(angle, vector)

    @classmethod
    def from_scale(cls: type[Mat4], vector: Vec3) -> Mat4:
        """Create a scale matrix from a Vec3."""
        return cls(vector.x, 0.0, 0.0, 0.0,
                   0.0, vector.y, 0.0, 0.0,
                   0.0, 0.0, vector.z, 0.0,
                   0.0, 0.0, 0.0, 1.0)

    @classmethod
    def from_translation(cls: type[Mat4], vector: Vec3) -> Mat4:
        """Create a translation matrix from a Vec3."""
        return cls(1.0, 0.0, 0.0, 0.0,
                   0.0, 1.0, 0.0, 0.0,
                   0.0, 0.0, 1.0, 0.0,
                   vector.x, vector.y, vector.z, 1.0)

    @classmethod
    def look_at(cls: type[Mat4], position: Vec3, target: Vec3, up: Vec3) -> Mat4:
        """Create a viewing matrix that points toward a target.

        This method takes three Vec3s, describing the viewer's position,
        where they are looking, and the upward axis (typically positive
        on the Y axis). The resulting Mat4 can be used as the projection
        matrix.

        Args:
          position: The location of the viewer in the scene.
          target: The point that the viewer is looking towards.
          up: A vector pointing "up" in the scene, typically `Vec3(0.0, 1.0, 0.0)`.
        """
        f = (target - position).normalize()
        u = up.normalize()
        s = f.cross(u).normalize()
        u = s.cross(f)

        return cls(s.x, u.x, -f.x, 0.0,
                   s.y, u.y, -f.y, 0.0,
                   s.z, u.z, -f.z, 0.0,
                   -s.dot(position), -u.dot(position), f.dot(position), 1.0)

    def row(self, index: int) -> tuple:
        """Get a specific row as a tuple."""
        return self[index::4]

    def column(self, index: int) -> tuple:
        """Get a specific column as a tuple."""
        return self[index * 4: index * 4 + 4]

    def rotate(self, angle: float, vector: Vec3) -> Mat4:
        """Get a rotation Matrix on x, y, or z axis."""
        if not all(abs(n) <= 1 for n in vector):
            raise ValueError("vector must be normalized (<=1)")
        x, y, z = vector
        c = _math.cos(angle)
        s = _math.sin(angle)
        t = 1 - c
        temp_x, temp_y, temp_z = t * x, t * y, t * z

        ra = c + temp_x * x
        rb = 0 + temp_x * y + s * z
        rc = 0 + temp_x * z - s * y
        re = 0 + temp_y * x - s * z
        rf = c + temp_y * y
        rg = 0 + temp_y * z + s * x
        ri = 0 + temp_z * x + s * y
        rj = 0 + temp_z * y - s * x
        rk = c + temp_z * z

        # ra, rb, rc, --
        # re, rf, rg, --
        # ri, rj, rk, --
        # --, --, --, --

        return self @ Mat4(ra, rb, rc, 0, re, rf, rg, 0, ri, rj, rk, 0, 0, 0, 0, 1)

    def scale(self, vector: Vec3) -> Mat4:
        """Get a scale Matrix on x, y, or z axis."""
        temp = list(self)
        temp[0] *= vector[0]
        temp[5] *= vector[1]
        temp[10] *= vector[2]
        return Mat4(*temp)

    def translate(self, vector: Vec3) -> Mat4:
        """Get a translation Matrix along x, y, and z axis."""
        return self @ Mat4(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, *vector, 1)

    def transpose(self) -> Mat4:
        """Get a transpose of this Matrix."""
        return Mat4(*self[0::4], *self[1::4], *self[2::4], *self[3::4])

    def __add__(self, other: Mat4) -> Mat4:
        if not isinstance(other, Mat4):
            raise TypeError("Can only add to other Mat4 types")
        return Mat4(*(s + o for s, o in zip(self, other)))

    def __sub__(self, other: Mat4) -> Mat4:
        if not isinstance(other, Mat4):
            raise TypeError("Can only subtract from other Mat4 types")
        return Mat4(*(s - o for s, o in zip(self, other)))

    def __pos__(self) -> Mat4:
        return self

    def __neg__(self) -> Mat4:
        return Mat4(*(-v for v in self))

    def __invert__(self) -> Mat4:
        # extract the elements in row-column form. (matrix is stored column first)
        a11, a12, a13, a14, a21, a22, a23, a24, a31, a32, a33, a34, a41, a42, a43, a44 = self

        a = a33 * a44 - a34 * a43
        b = a32 * a44 - a34 * a42
        c = a32 * a43 - a33 * a42
        d = a31 * a44 - a34 * a41
        e = a31 * a43 - a33 * a41
        f = a31 * a42 - a32 * a41
        g = a23 * a44 - a24 * a43
        h = a22 * a44 - a24 * a42
        i = a22 * a43 - a23 * a42
        j = a23 * a34 - a24 * a33
        k = a22 * a34 - a24 * a32
        l = a22 * a33 - a23 * a32
        m = a21 * a44 - a24 * a41
        n = a21 * a43 - a23 * a41
        o = a21 * a34 - a24 * a31
        p = a21 * a33 - a23 * a31
        q = a21 * a42 - a22 * a41
        r = a21 * a32 - a22 * a31

        det = (a11 * (a22 * a - a23 * b + a24 * c) -
               a12 * (a21 * a - a23 * d + a24 * e) +
               a13 * (a21 * b - a22 * d + a24 * f) -
               a14 * (a21 * c - a22 * e + a23 * f))

        if det == 0:
            _warnings.warn("Unable to calculate inverse of singular Matrix")
            return self

        pdet = 1 / det
        ndet = -pdet

        return Mat4(pdet * (a22 * a - a23 * b + a24 * c),
                    ndet * (a12 * a - a13 * b + a14 * c),
                    pdet * (a12 * g - a13 * h + a14 * i),
                    ndet * (a12 * j - a13 * k + a14 * l),
                    ndet * (a21 * a - a23 * d + a24 * e),
                    pdet * (a11 * a - a13 * d + a14 * e),
                    ndet * (a11 * g - a13 * m + a14 * n),
                    pdet * (a11 * j - a13 * o + a14 * p),
                    pdet * (a21 * b - a22 * d + a24 * f),
                    ndet * (a11 * b - a12 * d + a14 * f),
                    pdet * (a11 * h - a12 * m + a14 * q),
                    ndet * (a11 * k - a12 * o + a14 * r),
                    ndet * (a21 * c - a22 * e + a23 * f),
                    pdet * (a11 * c - a12 * e + a13 * f),
                    ndet * (a11 * i - a12 * n + a13 * q),
                    pdet * (a11 * l - a12 * p + a13 * r))

    def __round__(self, ndigits: int | None) -> Mat4:
        return Mat4(*(round(v, ndigits) for v in self))

    def __mul__(self, other: int) -> _typing.NoReturn:
        msg = "Please use the @ operator for Matrix multiplication."
        raise NotImplementedError(msg)

    @_typing.overload
    def __matmul__(self, other: Vec4) -> Vec4: ...

    @_typing.overload
    def __matmul__(self, other: Mat4) -> Mat4: ...

    def __matmul__(self, other):
        if isinstance(other, Vec4):
            x, y, z, w = other
            # extract the elements in row-column form. (matrix is stored column first)
            a11, a12, a13, a14, a21, a22, a23, a24, a31, a32, a33, a34, a41, a42, a43, a44 = self
            return Vec4(
                x * a11 + y * a21 + z * a31 + w * a41,
                x * a12 + y * a22 + z * a32 + w * a42,
                x * a13 + y * a23 + z * a33 + w * a43,
                x * a14 + y * a24 + z * a34 + w * a44,
            )

        if not isinstance(other, Mat4):
            msg = "Can only multiply with Mat4 or Vec4 types"
            raise TypeError(msg)

        # extract the elements in row-column form. (matrix is stored column first)
        a11, a12, a13, a14, a21, a22, a23, a24, a31, a32, a33, a34, a41, a42, a43, a44 = self
        b11, b12, b13, b14, b21, b22, b23, b24, b31, b32, b33, b34, b41, b42, b43, b44 = other
        # Multiply and sum rows * columns:
        return Mat4(
            # Column 1
            a11 * b11 + a21 * b12 + a31 * b13 + a41 * b14, a12 * b11 + a22 * b12 + a32 * b13 + a42 * b14,
            a13 * b11 + a23 * b12 + a33 * b13 + a43 * b14, a14 * b11 + a24 * b12 + a34 * b13 + a44 * b14,
            # Column 2
            a11 * b21 + a21 * b22 + a31 * b23 + a41 * b24, a12 * b21 + a22 * b22 + a32 * b23 + a42 * b24,
            a13 * b21 + a23 * b22 + a33 * b23 + a43 * b24, a14 * b21 + a24 * b22 + a34 * b23 + a44 * b24,
            # Column 3
            a11 * b31 + a21 * b32 + a31 * b33 + a41 * b34, a12 * b31 + a22 * b32 + a32 * b33 + a42 * b34,
            a13 * b31 + a23 * b32 + a33 * b33 + a43 * b34, a14 * b31 + a24 * b32 + a34 * b33 + a44 * b34,
            # Column 4
            a11 * b41 + a21 * b42 + a31 * b43 + a41 * b44, a12 * b41 + a22 * b42 + a32 * b43 + a42 * b44,
            a13 * b41 + a23 * b42 + a33 * b43 + a43 * b44, a14 * b41 + a24 * b42 + a34 * b43 + a44 * b44,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self[0:4]}\n    {self[4:8]}\n    {self[8:12]}\n    {self[12:16]}"


class Quaternion(_typing.NamedTuple):
    """Quaternion."""

    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    @classmethod
    def from_mat3(cls) -> Quaternion:
        raise NotImplementedError

    @classmethod
    def from_mat4(cls) -> Quaternion:
        raise NotImplementedError

    def to_mat4(self) -> Mat4:
        w = self.w
        x = self.x
        y = self.y
        z = self.z

        a = 1 - (y**2 + z**2) * 2
        b = 2 * (x * y - z * w)
        c = 2 * (x * z + y * w)

        e = 2 * (x * y + z * w)
        f = 1 - (x**2 + z**2) * 2
        g = 2 * (y * z - x * w)

        i = 2 * (x * z - y * w)
        j = 2 * (y * z + x * w)
        k = 1 - (x**2 + y**2) * 2

        # a, b, c, -
        # e, f, g, -
        # i, j, k, -
        # -, -, -, -

        return Mat4(a, b, c, 0.0, e, f, g, 0.0, i, j, k, 0.0, 0.0, 0.0, 0.0, 1.0)

    def to_mat3(self) -> Mat3:
        w = self.w
        x = self.x
        y = self.y
        z = self.z

        a = 1 - (y**2 + z**2) * 2
        b = 2 * (x * y - z * w)
        c = 2 * (x * z + y * w)

        e = 2 * (x * y + z * w)
        f = 1 - (x**2 + z**2) * 2
        g = 2 * (y * z - x * w)

        i = 2 * (x * z - y * w)
        j = 2 * (y * z + x * w)
        k = 1 - (x**2 + y**2) * 2

        # a, b, c, -
        # e, f, g, -
        # i, j, k, -
        # -, -, -, -

        return Mat3(*(a, b, c, e, f, g, i, j, k))

    def length(self) -> float:
        """Calculate the length of the Quaternion.

        The distance between the coordinates and the origin.
        """
        return _math.sqrt(self.w**2 + self.x**2 + self.y**2 + self.z**2)

    def conjugate(self) -> Quaternion:
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def dot(self, other: Quaternion) -> float:
        a, b, c, d = self
        e, f, g, h = other
        return a * e + b * f + c * g + d * h

    def normalize(self) -> Quaternion:
        m = self.length()
        if m == 0:
            return self
        return Quaternion(self.w / m, self.x / m, self.y / m, self.z / m)

    def __add__(self, other: Quaternion) -> Quaternion:
        a, b, c, d = self
        e, f, g, h = other
        return Quaternion(a + e, b + f, c + g, d + h)

    def __sub__(self, other: Quaternion) -> Quaternion:
        a, b, c, d = self
        e, f, g, h = other
        return Quaternion(a - e, b - f, c - g, d - h)

    def __mul__(self, scalar: float) -> Quaternion:
        w, x = self.w * scalar, self.x * scalar
        y, z = self.y * scalar, self.z * scalar
        return Quaternion(w, x, y, z)

    def __truediv__(self, other: Quaternion) -> Quaternion:
        return ~self @ other

    def __invert__(self) -> Quaternion:
        return self.conjugate() * (1 / self.dot(self))

    def __matmul__(self, other: Quaternion) -> Quaternion:
        a, u = self.w, Vec3(*self[1:])
        b, v = other.w, Vec3(*other[1:])
        scalar = a * b - u.dot(v)
        vector = v * a + u * b + u.cross(v)
        return Quaternion(scalar, *vector)
