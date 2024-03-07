"""Matrix and Vector math.

This module provides Vector and Matrix objects, including Vec2, Vec3,
Vec4, Mat3, and Mat4. Most common matrix and vector operations are
supported. Helper methods are included for rotating, scaling, and
transforming. The :py:class:`~pyglet.matrix.Mat4` includes class methods
for creating orthographic and perspective projection matrixes.

Matrices behave just like they do in GLSL: they are specified in column-major
order and multiply on the left of vectors, which are treated as columns.

.. note:: For performance reasons, Matrix types subclass `tuple`. They are
          therefore immutable. All operations return a new object; the object
          is not updated in-place.
"""

from __future__ import annotations

import math as _math
import typing as _typing
import warnings as _warnings

from collections.abc import Iterable as _Iterable

try:
    from math import sumprod as _sumprod
except ImportError:
    from operator import mul as _mul

    # TODO: remove Python < 3.12 fallback when 3.11 is EOL
    def _sumprod(p, q, /):
        return sum(map(_mul, p, q))


Mat3T = _typing.TypeVar("Mat3T", bound="Mat3")
Mat4T = _typing.TypeVar("Mat4T", bound="Mat4")


def clamp(num: float, min_val: float, max_val: float) -> float:
    return max(min(num, max_val), min_val)


class Vec2(tuple):
    """A two-dimensional vector represented as an X Y coordinate pair."""

    def __new__(cls, *args):
        assert len(args) in (0, 2), "0 or 2 values are required for Vec2 types."
        return super().__new__(Vec2, args or (0, 0))

    @property
    def x(self) -> float:
        return self[0]

    @property
    def y(self) -> float:
        return self[1]

    def __len__(self) -> int:
        return 2

    def __hash__(self) -> int:
        return super().__hash__()

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self[0] + other[0], self[1] + other[1])

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self[0] - other[0], self[1] - other[1])

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self[0] * scalar, self[1] * scalar)

    def __truediv__(self, scalar: float) -> Vec2:
        return Vec2(self[0] / scalar, self[1] / scalar)

    def __floordiv__(self, scalar: float) -> Vec2:
        return Vec2(self[0] // scalar, self[1] // scalar)

    def __abs__(self) -> float:
        return _math.sqrt(self[0] ** 2 + self[1] ** 2)

    def __neg__(self) -> Vec2:
        return Vec2(-self[0], -self[1])

    def __round__(self, ndigits: int | None = None) -> Vec2:
        return Vec2(*(round(v, ndigits) for v in self))

    def __radd__(self, other: Vec2 | int) -> Vec2:
        """Reverse add. Required for functionality with sum()
        """
        if other == 0:
            return self
        else:
            return self.__add__(_typing.cast(Vec2, other))

    def __lt__(self, other: Vec2) -> bool:
        return abs(self) < abs(other)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Vec2) and self[0] == other[0] and self[1] == other[1]

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Vec2) or self[0] != other[0] or self[1] != other[1]

    @staticmethod
    def from_polar(mag: float, angle: float) -> Vec2:
        """Create a new vector from the given polar coordinates.

        :parameters:
            `mag`   : int or float :
                The magnitude of the vector.
            `angle` : int or float :
                The angle of the vector in radians.
        """
        return Vec2(mag * _math.cos(angle), mag * _math.sin(angle))

    def from_magnitude(self, magnitude: float) -> Vec2:
        """Create a new Vector of the given magnitude by normalizing,
        then scaling the vector. The heading remains unchanged.

        :parameters:
            `magnitude` : int or float :
                The magnitude of the new vector.
        """
        return self.normalize() * magnitude

    def from_heading(self, heading: float) -> Vec2:
        """Create a new vector of the same magnitude with the given heading. I.e. Rotate the vector to the heading.

        :parameters:
            `heading` : int or float :
                The angle of the new vector in radians.
        """
        mag = self.__abs__()
        return Vec2(mag * _math.cos(heading), mag * _math.sin(heading))

    @property
    def heading(self) -> float:
        """The angle of the vector in radians."""
        return _math.atan2(self[1], self[0])

    @property
    def mag(self) -> float:
        """The magnitude, or length of the vector. The distance between the coordinates and the origin.

        Alias of abs(self).
        """
        return self.__abs__()

    def limit(self, maximum: float) -> Vec2:
        """Limit the magnitude of the vector to passed maximum value."""
        if self[0] ** 2 + self[1] ** 2 > maximum * maximum:
            return self.from_magnitude(maximum)
        return self

    def lerp(self, other: Vec2, alpha: float) -> Vec2:
        """Create a new Vec2 linearly interpolated between this vector and another Vec2.

        :parameters:
            `other`  : Vec2 :
                The vector to linearly interpolate with.
            `alpha` : float or int :
                The amount of interpolation.
                Some value between 0.0 (this vector) and 1.0 (other vector).
                0.5 is halfway inbetween.
        """
        return Vec2(self[0] + (alpha * (other[0] - self[0])),
                    self[1] + (alpha * (other[1] - self[1])))

    def reflect(self, normal: Vec2) -> Vec2:
        """Create a new Vec2 reflected (ricochet) from the given normal."""
        return self - normal * 2 * normal.dot(self)

    def rotate(self, angle: float) -> Vec2:
        """Create a new Vector rotated by the angle. The magnitude remains unchanged."""
        s = _math.sin(angle)
        c = _math.cos(angle)
        return Vec2(c * self[0] - s * self[1], s * self[0] + c * self[1])

    def distance(self, other: Vec2) -> float:
        """Calculate the distance between this vector and another 2D vector."""
        return _math.sqrt(((other[0] - self[0]) ** 2) + ((other[1] - self[1]) ** 2))

    def normalize(self) -> Vec2:
        """Normalize the vector to have a magnitude of 1. i.e. make it a unit vector."""
        d = self.__abs__()
        if d:
            return Vec2(self[0] / d, self[1] / d)
        return self

    def clamp(self, min_val: float, max_val: float) -> Vec2:
        """Restrict the value of the X and Y components of the vector to be within the given values."""
        return Vec2(clamp(self[0], min_val, max_val), clamp(self[1], min_val, max_val))

    def dot(self, other: Vec2) -> float:
        """Calculate the dot product of this vector and another 2D vector."""
        return self[0] * other[0] + self[1] * other[1]

    def __getattr__(self, attrs: str) -> Vec2 | Vec3 | Vec4:
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}.get(len(attrs))
            return vec_class(*(self['xy'.index(c)] for c in attrs))
        except (ValueError, TypeError):
            raise AttributeError(f"'{self.__class__.__name__}' invalid attr(s): '{attrs}'. "
                                 f"Valid attributes are 'x', 'y'. "
                                 f"Swizzling can be done for Vec2, Vec3, and Vec4.")

    def __repr__(self) -> str:
        return f"Vec2({self[0]}, {self[1]})"


class Vec3(tuple):
    """A three-dimensional vector represented as X Y Z coordinates."""

    def __new__(cls, *args):
        assert len(args) in (0, 3), "0 or 3 values are required for Vec3 types."
        return super().__new__(Vec3, args or (0, 0, 0))

    @property
    def x(self) -> float:
        return self[0]

    @property
    def y(self) -> float:
        return self[1]

    @property
    def z(self) -> float:
        return self[2]

    @property
    def mag(self) -> float:
        """The magnitude, or length of the vector. The distance between the coordinates and the origin.

        Alias of abs(self).

        :type: float
        """
        return self.__abs__()

    def __len__(self) -> int:
        return 3

    def __hash__(self) -> int:
        return super().__hash__()

    def __add__(self, other: Vec3) -> Vec3:
        return Vec3(self[0] + other[0], self[1] + other[1], self[2] + other[2])

    def __sub__(self, other: Vec3) -> Vec3:
        return Vec3(self[0] - other[0], self[1] - other[1], self[2] - other[2])

    def __mul__(self, scalar: float) -> Vec3:
        return Vec3(self[0] * scalar, self[1] * scalar, self[2] * scalar)

    def __truediv__(self, scalar: float) -> Vec3:
        return Vec3(self[0] / scalar, self[1] / scalar, self[2] / scalar)

    def __floordiv__(self, scalar: float) -> Vec3:
        return Vec3(self[0] // scalar, self[1] // scalar, self[2] // scalar)

    def __abs__(self) -> float:
        return _math.sqrt(self[0] ** 2 + self[1] ** 2 + self[2] ** 2)

    def __neg__(self) -> Vec3:
        return Vec3(-self[0], -self[1], -self[2])

    def __round__(self, ndigits: int | None = None) -> Vec3:
        return Vec3(*(round(v, ndigits) for v in self))

    def __radd__(self, other: Vec3 | int) -> Vec3:
        """Reverse add. Required for functionality with sum()"""
        if other == 0:
            return self
        else:
            return self.__add__(_typing.cast(Vec3, other))

    def __lt__(self, other: Vec3) -> bool:
        return abs(self) < abs(other)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Vec3) and self[0] == other[0] and self[1] == other[1] and self[2] == other[2]

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Vec3) or self[0] != other[0] or self[1] != other[1] or self[2] != other[2]

    def from_magnitude(self, magnitude: float) -> Vec3:
        """Create a new Vector of the given magnitude by normalizing,
        then scaling the vector. The rotation remains unchanged.
        """
        return self.normalize() * magnitude

    def limit(self, maximum: float) -> Vec3:
        """Limit the magnitude of the vector to the passed maximum value."""
        if self[0] ** 2 + self[1] ** 2 + self[2] ** 2 > maximum * maximum * maximum:
            return self.from_magnitude(maximum)
        return self

    def cross(self, other: Vec3) -> Vec3:
        """Calculate the cross product of this vector and another 3D vector."""
        return Vec3((self[1] * other[2]) - (self[2] * other[1]),
                    (self[2] * other[0]) - (self[0] * other[2]),
                    (self[0] * other[1]) - (self[1] * other[0]))

    def dot(self, other: Vec3) -> float:
        """Calculate the dot product of this vector and another 3D vector."""
        return self[0] * other[0] + self[1] * other[1] + self[2] * other[2]

    def lerp(self, other: Vec3, alpha: float) -> Vec3:
        """Create a new Vec3 linearly interpolated between this vector and another Vec3.

        The `alpha` parameter dictates the amount of interpolation.
        This should be a value between 0.0 (this vector) and 1.0 (other vector).
        For example; 0.5 is the midway point between both vectors.
        """
        return Vec3(self[0] + (alpha * (other[0] - self[0])),
                    self[1] + (alpha * (other[1] - self[1])),
                    self[2] + (alpha * (other[2] - self[2])))

    def distance(self, other: Vec3) -> float:
        """Get the distance between this vector and another 3D vector."""
        return _math.sqrt(((other[0] - self[0]) ** 2) +
                          ((other[1] - self[1]) ** 2) +
                          ((other[2] - self[2]) ** 2))

    def normalize(self) -> Vec3:
        """Normalize the vector to have a magnitude of 1. i.e. make it a unit vector."""
        try:
            d = self.__abs__()
            return Vec3(self[0] / d, self[1] / d, self[2] / d)
        except ZeroDivisionError:
            return self

    def clamp(self, min_val: float, max_val: float) -> Vec3:
        """Restrict the value of the X, Y and Z components of the vector to be within the given values."""
        return Vec3(clamp(self[0], min_val, max_val),
                    clamp(self[1], min_val, max_val),
                    clamp(self[2], min_val, max_val))

    def __getattr__(self, attrs: str) -> Vec2 | Vec3 | Vec4:
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}.get(len(attrs))
            return vec_class(*(self['xyz'.index(c)] for c in attrs))
        except (ValueError, TypeError):
            raise AttributeError(f"'{self.__class__.__name__}' invalid attr(s): '{attrs}'. "
                                 f"Valid attributes are 'x', 'y', 'z'. "
                                 f"Swizzling can be done for Vec2, Vec3, and Vec4.")

    def __repr__(self) -> str:
        return f"Vec3({self[0]}, {self[1]}, {self[2]})"


class Vec4(tuple):
    """A four-dimensional vector represented as X Y Z W coordinates."""

    def __new__(cls, *args):
        assert len(args) in (0, 4), "0 or 4 values are required for Vec4 types."
        return super().__new__(Vec4, args or (0, 0, 0, 0))

    @property
    def x(self) -> float:
        return self[0]

    @property
    def y(self) -> float:
        return self[1]

    @property
    def z(self) -> float:
        return self[2]

    @property
    def w(self) -> float:
        return self[3]

    def __len__(self) -> int:
        return 4

    def __hash__(self) -> int:
        return super().__hash__()

    def __add__(self, other: Vec4) -> Vec4:
        return Vec4(self[0] + other[0], self[1] + other[1], self[2] + other[2], self[3] + other[3])

    def __sub__(self, other: Vec4) -> Vec4:
        return Vec4(self[0] - other[0], self[1] - other[1], self[2] - other[2], self[3] - other[3])

    def __mul__(self, scalar: float) -> Vec4:
        return Vec4(self[0] * scalar, self[1] * scalar, self[2] * scalar, self[3] * scalar)

    def __truediv__(self, scalar: float) -> Vec4:
        return Vec4(self[0] / scalar, self[1] / scalar, self[2] / scalar, self[3] / scalar)

    def __floordiv__(self, scalar: float) -> Vec4:
        return Vec4(self[0] // scalar, self[1] // scalar, self[2] // scalar, self[3] // scalar)

    def __abs__(self) -> float:
        return _math.sqrt(self[0] ** 2 + self[1] ** 2 + self[2] ** 2 + self[3] ** 2)

    def __neg__(self) -> Vec4:
        return Vec4(-self[0], -self[1], -self[2], -self[3])

    def __round__(self, ndigits: int | None = None) -> Vec4:
        return Vec4(*(round(v, ndigits) for v in self))

    def __radd__(self, other: Vec4 | int) -> Vec4:
        if other == 0:
            return self
        else:
            return self.__add__(_typing.cast(Vec4, other))

    def __lt__(self, other: Vec4) -> bool:
        return abs(self) < abs(other)

    def __eq__(self, other: object) -> bool:
        return (
                isinstance(other, Vec4)
                and self[0] == other[0]
                and self[1] == other[1]
                and self[2] == other[2]
                and self[3] == other[3]
        )

    def __ne__(self, other: object) -> bool:
        return (
                not isinstance(other, Vec4)
                or self[0] != other[0]
                or self[1] != other[1]
                or self[2] != other[2]
                or self[3] != other[3]
        )

    def lerp(self, other: Vec4, alpha: float) -> Vec4:
        """Create a new Vec4 linearly interpolated between this one and another Vec4.

        The `alpha` parameter dictates the amount of interpolation.
        This should be a value between 0.0 (this vector) and 1.0 (other vector).
        For example; 0.5 is the midway point between both vectors.
        """
        return Vec4(self[0] + (alpha * (other[0] - self[0])),
                    self[1] + (alpha * (other[1] - self[1])),
                    self[2] + (alpha * (other[2] - self[2])),
                    self[3] + (alpha * (other[3] - self[3])))

    def distance(self, other: Vec4) -> float:
        return _math.sqrt(((other[0] - self[0]) ** 2) +
                          ((other[1] - self[1]) ** 2) +
                          ((other[2] - self[2]) ** 2) +
                          ((other[3] - self[3]) ** 2))

    def normalize(self) -> Vec4:
        """Normalize the vector to have a magnitude of 1. i.e. make it a unit vector."""
        d = self.__abs__()
        if d:
            return Vec4(self[0] / d, self[1] / d, self[2] / d, self[3] / d)
        return self

    def clamp(self, min_val: float, max_val: float) -> Vec4:
        return Vec4(clamp(self[0], min_val, max_val),
                    clamp(self[1], min_val, max_val),
                    clamp(self[2], min_val, max_val),
                    clamp(self[3], min_val, max_val))

    def dot(self, other: Vec4) -> float:
        return self[0] * other[0] + self[1] * other[1] + self[2] * other[2] + self[3] * other[3]

    def __getattr__(self, attrs: str) -> Vec2 | Vec3 | Vec4:
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}.get(len(attrs))
            return vec_class(*(self['xyzw'.index(c)] for c in attrs))
        except (ValueError, TypeError):
            raise AttributeError(f"'{self.__class__.__name__}' invalid attr(s): '{attrs}'. "
                                 f"Valid attributes are 'x', 'y', 'z', 'w'. "
                                 f"Swizzling can be done for Vec2, Vec3, and Vec4.")

    def __repr__(self) -> str:
        return f"Vec4({self[0]}, {self[1]}, {self[2]}, {self[3]})"


class Mat3(tuple):
    """A 3x3 Matrix

    `Mat3` is an immutable 3x3 Matrix, including most common
    operators.

    A Matrix can be created with a list or tuple of 12 values.
    If no values are provided, an "identity matrix" will be created
    (1.0 on the main diagonal). Mat3 objects are immutable, so
    all operations return a new Mat3 object.

    .. note:: Matrix multiplication is performed using the "@" operator.
    """
    def __new__(cls: type[Mat3T], values: _Iterable[float] = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)) -> Mat3T:
        new = super().__new__(cls, values)
        assert len(new) == 9, "A 3x3 Matrix requires 9 values"
        return new

    def scale(self, sx: float, sy: float) -> Mat3:
        return self @ Mat3((1.0 / sx, 0.0, 0.0, 0.0, 1.0 / sy, 0.0, 0.0, 0.0, 1.0))

    def translate(self, tx: float, ty: float) -> Mat3:
        return self @ Mat3((1.0, 0.0, 0.0, 0.0, 1.0, 0.0, -tx, ty, 1.0))

    def rotate(self, phi: float) -> Mat3:
        s = _math.sin(_math.radians(phi))
        c = _math.cos(_math.radians(phi))
        return self @ Mat3((c, s, 0.0, -s, c, 0.0, 0.0, 0.0, 1.0))

    def shear(self, sx: float, sy: float) -> Mat3:
        return self @ Mat3((1.0, sy, 0.0, sx, 1.0, 0.0, 0.0, 0.0, 1.0))

    def __add__(self, other: Mat3) -> Mat3:
        if not isinstance(other, Mat3):
            raise TypeError("Can only add to other Mat3 types")
        return Mat3(s + o for s, o in zip(self, other))

    def __sub__(self, other: Mat3) -> Mat3:
        if not isinstance(other, Mat3):
            raise TypeError("Can only subtract from other Mat3 types")
        return Mat3(s - o for s, o in zip(self, other))

    def __pos__(self) -> Mat3:
        return self

    def __neg__(self) -> Mat3:
        return Mat3(-v for v in self)

    def __round__(self, ndigits: int | None = None) -> Mat3:
        return Mat3(round(v, ndigits) for v in self)

    def __mul__(self, other: object) -> _typing.NoReturn:
        raise NotImplementedError("Please use the @ operator for Matrix multiplication.")

    @_typing.overload
    def __matmul__(self, other: Vec3) -> Vec3:
        ...

    @_typing.overload
    def __matmul__(self, other: Mat3) -> Mat3:
        ...

    def __matmul__(self, other):
        if isinstance(other, Vec3):
            # Rows:
            r0 = self[0::3]
            r1 = self[1::3]
            r2 = self[2::3]
            return Vec3(_sumprod(r0, other),
                        _sumprod(r1, other),
                        _sumprod(r2, other))

        if not isinstance(other, Mat3):
            raise TypeError("Can only multiply with Mat3 or Vec3 types")

        # Rows:
        r0 = self[0::3]
        r1 = self[1::3]
        r2 = self[2::3]
        # Columns:
        c0 = other[0:3]
        c1 = other[3:6]
        c2 = other[6:9]

        # Multiply and sum rows * columns:
        return Mat3((_sumprod(c0, r0), _sumprod(c0, r1), _sumprod(c0, r2),
                     _sumprod(c1, r0), _sumprod(c1, r1), _sumprod(c1, r2),
                     _sumprod(c2, r0), _sumprod(c2, r1), _sumprod(c2, r2)))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self[0:3]}\n    {self[3:6]}\n    {self[6:9]}"


class Mat4(tuple):
    """A 4x4 Matrix

    `Mat4` is an immutable 4x4 Matrix, which includs most common
    operators. This includes class methods for creating orthogonal
    and perspective projection matrixes, to be used by OpenGL.

    A Matrix can be created with a list or tuple of 16 values.
    If no values are provided, an "identity matrix" will be created
    (1.0 on the main diagonal). Mat4 objects are immutable, so
    all operations return a new Mat4 object.

    .. note:: Matrix multiplication is performed using the "@" operator.
    """
    def __new__(cls: type[Mat4T], values: _Iterable[float] = (1.0, 0.0, 0.0, 0.0,
                                                              0.0, 1.0, 0.0, 0.0,
                                                              0.0, 0.0, 1.0, 0.0,
                                                              0.0, 0.0, 0.0, 1.0,)) -> Mat4T:
        new = super().__new__(cls, values)
        assert len(new) == 16, "A 4x4 Matrix requires 16 values"
        return new

    @classmethod
    def orthogonal_projection(cls: type[Mat4T], left: float, right: float, bottom: float, top: float, z_near: float, z_far: float) -> Mat4T:
        """Create a Mat4 orthographic projection matrix for use with OpenGL.

        Given left, right, bottom, top values, and near/far z planes,
        create a 4x4 Projection Matrix. This is useful for setting
        :py:attr:`~pyglet.window.Window.projection`.
        """
        width = right - left
        height = top - bottom
        depth = z_far - z_near

        sx = 2.0 / width
        sy = 2.0 / height
        sz = 2.0 / -depth

        tx = -(right + left) / width
        ty = -(top + bottom) / height
        tz = -(z_far + z_near) / depth

        return cls((sx, 0.0, 0.0, 0.0,
                    0.0, sy, 0.0, 0.0,
                    0.0, 0.0, sz, 0.0,
                    tx, ty, tz, 1.0))

    @classmethod
    def perspective_projection(cls: type[Mat4T], aspect: float, z_near: float, z_far: float, fov: float = 60) -> Mat4T:
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

        return cls((w, 0, 0, 0,
                    0, h, 0, 0,
                    0, 0, q, -1,
                    0, 0, qn, 0))

    @classmethod
    def from_rotation(cls, angle: float, vector: Vec3) -> Mat4:
        """Create a rotation matrix from an angle and Vec3."""
        return cls().rotate(angle, vector)

    @classmethod
    def from_scale(cls: type[Mat4T], vector: Vec3) -> Mat4T:
        """Create a scale matrix from a Vec3."""
        return cls((vector[0], 0.0, 0.0, 0.0,
                    0.0, vector[1], 0.0, 0.0,
                    0.0, 0.0, vector[2], 0.0,
                    0.0, 0.0, 0.0, 1.0))

    @classmethod
    def from_translation(cls: type[Mat4T], vector: Vec3) -> Mat4T:
        """Create a translation matrix from a Vec3."""
        return cls((1.0, 0.0, 0.0, 0.0,
                    0.0, 1.0, 0.0, 0.0,
                    0.0, 0.0, 1.0, 0.0,
                    vector[0], vector[1], vector[2], 1.0))

    @classmethod
    def look_at(cls: type[Mat4T], position: Vec3, target: Vec3, up: Vec3):
        f = (target - position).normalize()
        u = up.normalize()
        s = f.cross(u).normalize()
        u = s.cross(f)

        return cls([s.x, u.x, -f.x, 0.0,
                    s.y, u.y, -f.y, 0.0,
                    s.z, u.z, -f.z, 0.0,
                    -s.dot(position), -u.dot(position), f.dot(position), 1.0])

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

        return Mat4(self) @ Mat4((ra, rb, rc, 0, re, rf, rg, 0, ri, rj, rk, 0, 0, 0, 0, 1))

    def scale(self, vector: Vec3) -> Mat4:
        """Get a scale Matrix on x, y, or z axis."""
        temp = list(self)
        temp[0] *= vector[0]
        temp[5] *= vector[1]
        temp[10] *= vector[2]
        return Mat4(temp)

    def translate(self, vector: Vec3) -> Mat4:
        """Get a translation Matrix along x, y, and z axis."""
        return self @ Mat4((1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, *vector, 1))

    def transpose(self) -> Mat4:
        """Get a transpose of this Matrix."""
        return Mat4(self[0::4] + self[1::4] + self[2::4] + self[3::4])

    def __add__(self, other: Mat4) -> Mat4:
        if not isinstance(other, Mat4):
            raise TypeError("Can only add to other Mat4 types")
        return Mat4(s + o for s, o in zip(self, other))

    def __sub__(self, other: Mat4) -> Mat4:
        if not isinstance(other, Mat4):
            raise TypeError("Can only subtract from other Mat4 types")
        return Mat4(s - o for s, o in zip(self, other))

    def __pos__(self) -> Mat4:
        return self

    def __neg__(self) -> Mat4:
        return Mat4(-v for v in self)

    def __invert__(self) -> Mat4:
        a = self[10] * self[15] - self[11] * self[14]
        b = self[9] * self[15] - self[11] * self[13]
        c = self[9] * self[14] - self[10] * self[13]
        d = self[8] * self[15] - self[11] * self[12]
        e = self[8] * self[14] - self[10] * self[12]
        f = self[8] * self[13] - self[9] * self[12]
        g = self[6] * self[15] - self[7] * self[14]
        h = self[5] * self[15] - self[7] * self[13]
        i = self[5] * self[14] - self[6] * self[13]
        j = self[6] * self[11] - self[7] * self[10]
        k = self[5] * self[11] - self[7] * self[9]
        l = self[5] * self[10] - self[6] * self[9]
        m = self[4] * self[15] - self[7] * self[12]
        n = self[4] * self[14] - self[6] * self[12]
        o = self[4] * self[11] - self[7] * self[8]
        p = self[4] * self[10] - self[6] * self[8]
        q = self[4] * self[13] - self[5] * self[12]
        r = self[4] * self[9] - self[5] * self[8]

        det = (self[0] * (self[5] * a - self[6] * b + self[7] * c)
               - self[1] * (self[4] * a - self[6] * d + self[7] * e)
               + self[2] * (self[4] * b - self[5] * d + self[7] * f)
               - self[3] * (self[4] * c - self[5] * e + self[6] * f))

        if det == 0:
            _warnings.warn("Unable to calculate inverse of singular Matrix")
            return self

        pdet = 1 / det
        ndet = -pdet

        return Mat4((pdet * (self[5] * a - self[6] * b + self[7] * c),
                     ndet * (self[1] * a - self[2] * b + self[3] * c),
                     pdet * (self[1] * g - self[2] * h + self[3] * i),
                     ndet * (self[1] * j - self[2] * k + self[3] * l),
                     ndet * (self[4] * a - self[6] * d + self[7] * e),
                     pdet * (self[0] * a - self[2] * d + self[3] * e),
                     ndet * (self[0] * g - self[2] * m + self[3] * n),
                     pdet * (self[0] * j - self[2] * o + self[3] * p),
                     pdet * (self[4] * b - self[5] * d + self[7] * f),
                     ndet * (self[0] * b - self[1] * d + self[3] * f),
                     pdet * (self[0] * h - self[1] * m + self[3] * q),
                     ndet * (self[0] * k - self[1] * o + self[3] * r),
                     ndet * (self[4] * c - self[5] * e + self[6] * f),
                     pdet * (self[0] * c - self[1] * e + self[2] * f),
                     ndet * (self[0] * i - self[1] * n + self[2] * q),
                     pdet * (self[0] * l - self[1] * p + self[2] * r)))

    def __round__(self, ndigits: int | None = None) -> Mat4:
        return Mat4(round(v, ndigits) for v in self)

    def __mul__(self, other: int) -> _typing.NoReturn:
        raise NotImplementedError("Please use the @ operator for Matrix multiplication.")

    @_typing.overload
    def __matmul__(self, other: Vec4) -> Vec4:
        ...

    @_typing.overload
    def __matmul__(self, other: Mat4) -> Mat4:
        ...

    def __matmul__(self, other):
        if isinstance(other, Vec4):
            # Rows:
            r0 = self[0::4]
            r1 = self[1::4]
            r2 = self[2::4]
            r3 = self[3::4]
            return Vec4(_sumprod(r0, other),
                        _sumprod(r1, other),
                        _sumprod(r2, other),
                        _sumprod(r3, other))

        if not isinstance(other, Mat4):
            raise TypeError("Can only multiply with Mat4 or Vec4 types")
        # Rows:
        r0 = self[0::4]
        r1 = self[1::4]
        r2 = self[2::4]
        r3 = self[3::4]
        # Columns:
        c0 = other[0:4]
        c1 = other[4:8]
        c2 = other[8:12]
        c3 = other[12:16]

        # Multiply and sum rows * columns:
        return Mat4((_sumprod(c0, r0), _sumprod(c0, r1), _sumprod(c0, r2), _sumprod(c0, r3),
                     _sumprod(c1, r0), _sumprod(c1, r1), _sumprod(c1, r2), _sumprod(c1, r3),
                     _sumprod(c2, r0), _sumprod(c2, r1), _sumprod(c2, r2), _sumprod(c2, r3),
                     _sumprod(c3, r0), _sumprod(c3, r1), _sumprod(c3, r2), _sumprod(c3, r3)))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self[0:4]}\n    {self[4:8]}\n    {self[8:12]}\n    {self[12:16]}"


class Quaternion(tuple):
    """Quaternion"""

    def __new__(cls, w: float = 1.0, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Quaternion:
        return super().__new__(Quaternion, (w, x, y, z))

    @classmethod
    def from_mat3(cls) -> Quaternion:
        raise NotImplementedError("Not yet implemented")

    @classmethod
    def from_mat4(cls) -> Quaternion:
        raise NotImplementedError("Not yet implemented")

    def to_mat4(self) -> Mat4:
        w = self.w
        x = self.x
        y = self.y
        z = self.z

        a = 1 - (y ** 2 + z ** 2) * 2
        b = 2 * (x * y - z * w)
        c = 2 * (x * z + y * w)

        e = 2 * (x * y + z * w)
        f = 1 - (x ** 2 + z ** 2) * 2
        g = 2 * (y * z - x * w)

        i = 2 * (x * z - y * w)
        j = 2 * (y * z + x * w)
        k = 1 - (x ** 2 + y ** 2) * 2

        # a, b, c, -
        # e, f, g, -
        # i, j, k, -
        # -, -, -, -

        return Mat4((a, b, c, 0.0, e, f, g, 0.0, i, j, k, 0.0, 0.0, 0.0, 0.0, 1.0))

    def to_mat3(self) -> Mat3:
        w = self.w
        x = self.x
        y = self.y
        z = self.z

        a = 1 - (y ** 2 + z ** 2) * 2
        b = 2 * (x * y - z * w)
        c = 2 * (x * z + y * w)

        e = 2 * (x * y + z * w)
        f = 1 - (x ** 2 + z ** 2) * 2
        g = 2 * (y * z - x * w)

        i = 2 * (x * z - y * w)
        j = 2 * (y * z + x * w)
        k = 1 - (x ** 2 + y ** 2) * 2

        # a, b, c, -
        # e, f, g, -
        # i, j, k, -
        # -, -, -, -

        return Mat3((a, b, c, e, f, g, i, j, k))

    @property
    def w(self) -> float:
        return self[0]

    @property
    def x(self) -> float:
        return self[1]

    @property
    def y(self) -> float:
        return self[2]

    @property
    def z(self) -> float:
        return self[3]

    @property
    def mag(self) -> float:
        return self.__abs__()

    def conjugate(self) -> Quaternion:
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def dot(self, other: Quaternion) -> float:
        a, b, c, d = self
        e, f, g, h = other
        return a * e + b * f + c * g + d * h

    def normalize(self) -> Quaternion:
        m = self.__abs__()
        if m == 0:
            return self
        return Quaternion(self[0] / m, self[1] / m, self[2] / m, self[3] / m)

    def __abs__(self) -> float:
        return _math.sqrt(self.w ** 2 + self.x ** 2 + self.y ** 2 + self.z ** 2)

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
        a, u = self[0], Vec3(*self[1:])
        b, v = other[0], Vec3(*other[1:])
        scalar = a * b - u.dot(v)
        vector = v * a + u * b + u.cross(v)
        return Quaternion(scalar, *vector)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(w={self[0]}, x={self[1]}, y={self[2]}, z={self[3]})"
