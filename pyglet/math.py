"""Matrix and Vector math.

This module provides Vector and Matrix objects, including Vec2, Vec3,
Vec4, Mat3, and Mat4. Most common matrix and vector operations are
supported. Helper methods are included for rotating, scaling, and
transforming. The :py:class:`~pyglet.matrix.Mat4` includes class methods
for creating orthographic and perspective projection matrixes.

Matrices behave just like they do in GLSL: they are specified in column-major
order and multiply on the left of vectors, which are treated as columns.

:note: For performance, Matrixes subclass the `tuple` type. They
    are therefore immutable - all operations return a new object;
    the object is not updated in-place.
"""

from __future__ import annotations

import math as _math
import typing as _typing
import warnings as _warnings

from operator import mul as _mul
from collections.abc import Iterable as _Iterable
from collections.abc import Iterator as _Iterator


number = _typing.Union[float, int]
Mat4T = _typing.TypeVar("Mat4T", bound="Mat4")


def clamp(num: float, min_val: float, max_val: float) -> float:
    return max(min(num, max_val), min_val)


class Vec2:
    __slots__ = 'x', 'y'

    """A two-dimensional vector represented as an X Y coordinate pair."""

    def __init__(self, x: number = 0.0, y: number = 0.0) -> None:
        self.x = x
        self.y = y

    def __iter__(self) -> _Iterator[float]:
        yield self.x
        yield self.y

    @_typing.overload
    def __getitem__(self, item: int) -> float:
        ...

    @_typing.overload
    def __getitem__(self, item: slice) -> tuple[float, ...]:
        ...

    def __getitem__(self, item):
        return (self.x, self.y)[item]

    def __setitem__(self, key, value):
        if type(key) is slice:
            for i, attr in enumerate(['x', 'y'][key]):
                setattr(self, attr, value[i])
        else:
            setattr(self, ['x', 'y'][key], value)

    def __len__(self) -> int:
        return 2

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: number) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: number) -> Vec2:
        return Vec2(self.x / scalar, self.y / scalar)

    def __floordiv__(self, scalar: number) -> Vec2:
        return Vec2(self.x // scalar, self.y // scalar)

    def __abs__(self) -> float:
        return _math.sqrt(self.x ** 2 + self.y ** 2)

    def __neg__(self) -> Vec2:
        return Vec2(-self.x, -self.y)

    def __round__(self, ndigits: int | None = None) -> Vec2:
        return Vec2(*(round(v, ndigits) for v in self))

    def __radd__(self, other: Vec2 | int) -> Vec2:
        """Reverse add. Required for functionality with sum()
        """
        if other == 0:
            return self
        else:
            return self.__add__(_typing.cast(Vec2, other))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Vec2) and self.x == other.x and self.y == other.y

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Vec2) or self.x != other.x or self.y != other.y

    @staticmethod
    def from_polar(mag: float, angle: float) -> Vec2:
        """Create a new vector from the given polar coordinates.

        :parameters:
            `mag`   : int or float :
                The magnitude of the vector.
            `angle` : int or float :
                The angle of the vector in radians.

        :returns: A new vector with the given angle and magnitude.
        :rtype: Vec2
        """
        return Vec2(mag * _math.cos(angle), mag * _math.sin(angle))

    def from_magnitude(self, magnitude: float) -> Vec2:
        """Create a new Vector of the given magnitude by normalizing,
        then scaling the vector. The heading remains unchanged.

        :parameters:
            `magnitude` : int or float :
                The magnitude of the new vector.

        :returns: A new vector with the magnitude.
        :rtype: Vec2
        """
        return self.normalize() * magnitude

    def from_heading(self, heading: float) -> Vec2:
        """Create a new vector of the same magnitude with the given heading. I.e. Rotate the vector to the heading.

        :parameters:
            `heading` : int or float :
                The angle of the new vector in radians.

        :returns: A new vector with the given heading.
        :rtype: Vec2
        """
        mag = self.__abs__()
        return Vec2(mag * _math.cos(heading), mag * _math.sin(heading))

    @property
    def heading(self) -> float:
        """The angle of the vector in radians.

        :type: float
        """
        return _math.atan2(self.y, self.x)

    @property
    def mag(self) -> float:
        """The magnitude, or length of the vector. The distance between the coordinates and the origin.

        Alias of abs(self).

        :type: float
        """
        return self.__abs__()

    def limit(self, maximum: float) -> Vec2:
        """Limit the magnitude of the vector to the value used for the max parameter.

        :parameters:
            `maximum`  : int or float :
                The maximum magnitude for the vector.

        :returns: Either self or a new vector with the maximum magnitude.
        :rtype: Vec2
        """
        if self.x ** 2 + self.y ** 2 > maximum * maximum:
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

        :returns: A new interpolated vector.
        :rtype: Vec2
        """
        return Vec2(self.x + (alpha * (other.x - self.x)),
                    self.y + (alpha * (other.y - self.y)))

    def reflect(self, normal: Vec2) -> Vec2:
        """Create a new Vec2 reflected (ricochet) from the given normal."""
        return self - normal * 2 * normal.dot(self)

    def rotate(self, angle: float) -> Vec2:
        """Create a new Vector rotated by the angle. The magnitude remains unchanged.

        :parameters:
            `angle` : int or float :
                The angle to rotate by

        :returns: A new rotated vector of the same magnitude.
        :rtype: Vec2
        """
        s = _math.sin(angle)
        c = _math.cos(angle)
        return Vec2(c * self.x - s * self.y, s * self.x + c * self.y)

    def distance(self, other: Vec2) -> float:
        """Calculate the distance between this vector and another 2D vector."""
        return _math.sqrt(((other.x - self.x) ** 2) + ((other.y - self.y) ** 2))

    def normalize(self) -> Vec2:
        """Normalize the vector to have a magnitude of 1. i.e. make it a unit vector.

        :returns: A unit vector with the same heading.
        :rtype: Vec2
        """
        d = self.__abs__()
        if d:
            return Vec2(self.x / d, self.y / d)
        return self

    def clamp(self, min_val: float, max_val: float) -> Vec2:
        """Restrict the value of the X and Y components of the vector to be within the given values.

        :parameters:
            `min_val` : int or float :
                The minimum value
            `max_val` : int or float :
                The maximum value

        :returns: A new vector with clamped X and Y components.
        :rtype: Vec2
        """
        return Vec2(clamp(self.x, min_val, max_val), clamp(self.y, min_val, max_val))

    def dot(self, other: Vec2) -> float:
        """Calculate the dot product of this vector and another 2D vector.

        :parameters:
            `other`  : Vec2 :
                The other vector.

        :returns: The dot product of the two vectors.
        :rtype: float
        """
        return self.x * other.x + self.y * other.y

    def __getattr__(self, attrs: str) -> Vec2 | Vec3 | Vec4:
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}[len(attrs)]
            return vec_class(*(self['xy'.index(c)] for c in attrs))
        except Exception:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{attrs}'"
            ) from None

    def __repr__(self) -> str:
        return f"Vec2({self.x}, {self.y})"


class Vec3:
    __slots__ = 'x', 'y', 'z'

    """A three-dimensional vector represented as X Y Z coordinates."""

    def __init__(self, x: number = 0.0, y: number = 0.0, z: number = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z

    def __iter__(self) -> _Iterator[float]:
        yield self.x
        yield self.y
        yield self.z

    @_typing.overload
    def __getitem__(self, item: int) -> float:
        ...

    @_typing.overload
    def __getitem__(self, item: slice) -> tuple[float, ...]:
        ...

    def __getitem__(self, item):
        return (self.x, self.y, self.z)[item]

    def __setitem__(self, key, value):
        if type(key) is slice:
            for i, attr in enumerate(['x', 'y', 'z'][key]):
                setattr(self, attr, value[i])
        else:
            setattr(self, ['x', 'y', 'z'][key], value)

    def __len__(self) -> int:
        return 3

    @property
    def mag(self) -> float:
        """The magnitude, or length of the vector. The distance between the coordinates and the origin.

        Alias of abs(self).

        :type: float
        """
        return self.__abs__()

    def __add__(self, other: Vec3) -> Vec3:
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vec3) -> Vec3:
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: number) -> Vec3:
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __truediv__(self, scalar: number) -> Vec3:
        return Vec3(self.x / scalar, self.y / scalar, self.z / scalar)

    def __floordiv__(self, scalar: number) -> Vec3:
        return Vec3(self.x // scalar, self.y // scalar, self.z // scalar)

    def __abs__(self) -> float:
        return _math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def __neg__(self) -> Vec3:
        return Vec3(-self.x, -self.y, -self.z)

    def __round__(self, ndigits: int | None = None) -> Vec3:
        return Vec3(*(round(v, ndigits) for v in self))

    def __radd__(self, other: Vec3 | int) -> Vec3:
        """Reverse add. Required for functionality with sum()"""
        if other == 0:
            return self
        else:
            return self.__add__(_typing.cast(Vec3, other))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Vec3) and self.x == other.x and self.y == other.y and self.z == other.z

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Vec3) or self.x != other.x or self.y != other.y or self.z != other.z

    def from_magnitude(self, magnitude: float) -> Vec3:
        """Create a new Vector of the given magnitude by normalizing,
        then scaling the vector. The rotation remains unchanged.

        :parameters:
            `magnitude` : int or float :
                The magnitude of the new vector.

        :returns: A new vector with the magnitude.
        :rtype: Vec3
        """
        return self.normalize() * magnitude

    def limit(self, maximum: float) -> Vec3:
        """Limit the magnitude of the vector to the value used for the max parameter.

        :parameters:
            `maximum`  : int or float :
                The maximum magnitude for the vector.

        :returns: Either self or a new vector with the maximum magnitude.
        :rtype: Vec3
        """
        if self.x ** 2 + self.y ** 2 + self.z ** 2 > maximum * maximum * maximum:
            return self.from_magnitude(maximum)
        return self

    def cross(self, other: Vec3) -> Vec3:
        """Calculate the cross product of this vector and another 3D vector.

        :parameters:
            `other`  : Vec3 :
                The other vector.

        :returns: The cross product of the two vectors.
        :rtype: float
        """
        return Vec3((self.y * other.z) - (self.z * other.y),
                    (self.z * other.x) - (self.x * other.z),
                    (self.x * other.y) - (self.y * other.x))

    def dot(self, other: Vec3) -> float:
        """Calculate the dot product of this vector and another 3D vector.

        :parameters:
            `other`  : Vec3 :
                The other vector.

        :returns: The dot product of the two vectors.
        :rtype: float
        """
        return self.x * other.x + self.y * other.y + self.z * other.z

    def lerp(self, other: Vec3, alpha: float) -> Vec3:
        """Create a new Vec3 linearly interpolated between this vector and another Vec3.

        :parameters:
            `other`  : Vec3 :
                The vector to linearly interpolate with.
            `alpha` : float or int :
                The amount of interpolation.
                Some value between 0.0 (this vector) and 1.0 (other vector).
                0.5 is halfway inbetween.

        :returns: A new interpolated vector.
        :rtype: Vec3
        """
        return Vec3(self.x + (alpha * (other.x - self.x)),
                    self.y + (alpha * (other.y - self.y)),
                    self.z + (alpha * (other.z - self.z)))

    def distance(self, other: Vec3) -> float:
        """Calculate the distance between this vector and another 3D vector.

        :parameters:
            `other`  : Vec3 :
                The other vector

        :returns: The distance between the two vectors.
        :rtype: float
        """
        return _math.sqrt(((other.x - self.x) ** 2) +
                          ((other.y - self.y) ** 2) +
                          ((other.z - self.z) ** 2))

    def normalize(self) -> Vec3:
        """Normalize the vector to have a magnitude of 1. i.e. make it a unit vector.

        :returns: A unit vector with the same rotation.
        :rtype: Vec3
        """
        try:
            d = self.__abs__()
            return Vec3(self.x / d, self.y / d, self.z / d)
        except ZeroDivisionError:
            return self

    def clamp(self, min_val: float, max_val: float) -> Vec3:
        """Restrict the value of the X,  Y and Z components of the vector to be within the given values.

        :parameters:
            `min_val` : int or float :
                The minimum value
            `max_val` : int or float :
                The maximum value

        :returns: A new vector with clamped X, Y and Z components.
        :rtype: Vec3
        """
        return Vec3(clamp(self.x, min_val, max_val),
                    clamp(self.y, min_val, max_val),
                    clamp(self.z, min_val, max_val))

    def __getattr__(self, attrs: str) -> Vec2 | Vec3 | Vec4:
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}[len(attrs)]
            return vec_class(*(self['xyz'.index(c)] for c in attrs))
        except Exception:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{attrs}'"
            ) from None

    def __repr__(self) -> str:
        return f"Vec3({self.x}, {self.y}, {self.z})"


class Vec4:
    __slots__ = 'x', 'y', 'z', 'w'

    """A four-dimensional vector represented as X Y Z W coordinates."""

    def __init__(self, x: number = 0.0, y: number = 0.0, z: number = 0.0, w: number = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def __iter__(self) -> _Iterator[float]:
        yield self.x
        yield self.y
        yield self.z
        yield self.w

    @_typing.overload
    def __getitem__(self, item: int) -> float:
        ...

    @_typing.overload
    def __getitem__(self, item: slice) -> tuple[float, ...]:
        ...

    def __getitem__(self, item):
        return (self.x, self.y, self.z, self.w)[item]

    def __setitem__(self, key, value):
        if type(key) is slice:
            for i, attr in enumerate(['x', 'y', 'z', 'w'][key]):
                setattr(self, attr, value[i])
        else:
            setattr(self, ['x', 'y', 'z', 'w'][key], value)

    def __len__(self) -> int:
        return 4

    def __add__(self, other: Vec4) -> Vec4:
        return Vec4(self.x + other.x, self.y + other.y, self.z + other.z, self.w + other.w)

    def __sub__(self, other: Vec4) -> Vec4:
        return Vec4(self.x - other.x, self.y - other.y, self.z - other.z, self.w - other.w)

    def __mul__(self, scalar: number) -> Vec4:
        return Vec4(self.x * scalar, self.y * scalar, self.z * scalar, self.w * scalar)

    def __truediv__(self, scalar: number) -> Vec4:
        return Vec4(self.x / scalar, self.y / scalar, self.z / scalar, self.w / scalar)

    def __floordiv__(self, scalar: number) -> Vec4:
        return Vec4(self.x // scalar, self.y // scalar, self.z // scalar, self.w // scalar)

    def __abs__(self) -> float:
        return _math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2 + self.w ** 2)

    def __neg__(self) -> Vec4:
        return Vec4(-self.x, -self.y, -self.z, -self.w)

    def __round__(self, ndigits: int | None = None) -> Vec4:
        return Vec4(*(round(v, ndigits) for v in self))

    def __radd__(self, other: Vec4 | int) -> Vec4:
        if other == 0:
            return self
        else:
            return self.__add__(_typing.cast(Vec4, other))

    def __eq__(self, other: object) -> bool:
        return (
                isinstance(other, Vec4)
                and self.x == other.x
                and self.y == other.y
                and self.z == other.z
                and self.w == other.w
        )

    def __ne__(self, other: object) -> bool:
        return (
                not isinstance(other, Vec4)
                or self.x != other.x
                or self.y != other.y
                or self.z != other.z
                or self.w != other.w
        )

    def lerp(self, other: Vec4, alpha: float) -> Vec4:
        """Create a new Vec4 linearly interpolated between this one and another Vec4.

        :parameters:
            `other`  : Vec4 :
                The vector to linearly interpolate with.
            `alpha` : float or int :
                The amount of interpolation.
                Some value between 0.0 (this vector) and 1.0 (other vector).
                0.5 is halfway inbetween.

        :returns: A new interpolated vector.
        :rtype: Vec4
        """
        return Vec4(self.x + (alpha * (other.x - self.x)),
                    self.y + (alpha * (other.y - self.y)),
                    self.z + (alpha * (other.z - self.z)),
                    self.w + (alpha * (other.w - self.w)))

    def distance(self, other: Vec4) -> float:
        return _math.sqrt(((other.x - self.x) ** 2) +
                          ((other.y - self.y) ** 2) +
                          ((other.z - self.z) ** 2) +
                          ((other.w - self.w) ** 2))

    def normalize(self) -> Vec4:
        """Normalize the vector to have a magnitude of 1. i.e. make it a unit vector."""
        d = self.__abs__()
        if d:
            return Vec4(self.x / d, self.y / d, self.z / d, self.w / d)
        return self

    def clamp(self, min_val: float, max_val: float) -> Vec4:
        return Vec4(clamp(self.x, min_val, max_val),
                    clamp(self.y, min_val, max_val),
                    clamp(self.z, min_val, max_val),
                    clamp(self.w, min_val, max_val))

    def dot(self, other: Vec4) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z + self.w * other.w

    def __getattr__(self, attrs: str) -> Vec2 | Vec3 | Vec4:
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}[len(attrs)]
            return vec_class(*(self['xyzw'.index(c)] for c in attrs))
        except Exception:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{attrs}'"
            ) from None

    def __repr__(self) -> str:
        return f"Vec4({self.x}, {self.y}, {self.z}, {self.w})"


class Mat3(tuple):
    """A 3x3 Matrix class

    `Mat3` is an immutable 3x3 Matrix, including most common
    operators. Matrix multiplication must be performed using
    the "@" operator.
    """

    def __new__(cls, values: _Iterable[float] = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)) -> Mat3:
        """Create a 3x3 Matrix

        A Mat3 can be created with a list or tuple of 9 values.
        If no values are provided, an "identity matrix" will be created
        (1.0 on the main diagonal). Matrix objects are immutable, so
        all operations return a new Mat3 object.

        :Parameters:
            `values` : tuple of float or int
                A tuple or list containing 9 floats or ints.
        """
        new = super().__new__(Mat3, values)
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
            return Vec3(sum(map(_mul, r0, other)),
                        sum(map(_mul, r1, other)),
                        sum(map(_mul, r2, other)))

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
        return Mat3((sum(map(_mul, c0, r0)), sum(map(_mul, c0, r1)), sum(map(_mul, c0, r2)),
                     sum(map(_mul, c1, r0)), sum(map(_mul, c1, r1)), sum(map(_mul, c1, r2)),
                     sum(map(_mul, c2, r0)), sum(map(_mul, c2, r1)), sum(map(_mul, c2, r2))))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self[0:3]}\n    {self[3:6]}\n    {self[6:9]}"


class Mat4(tuple):
    """A 4x4 Matrix class

    `Mat4` is an immutable 4x4 Matrix, including most common
    operators. Matrix multiplication must be performed using
    the "@" operator.
    Class methods are available for creating orthogonal
    and perspective projections matrixes.
    """

    def __new__(cls, values: _Iterable[float] = (1.0, 0.0, 0.0, 0.0,
                                                 0.0, 1.0, 0.0, 0.0,
                                                 0.0, 0.0, 1.0, 0.0,
                                                 0.0, 0.0, 0.0, 1.0,)) -> Mat4:
        """Create a 4x4 Matrix

        A Matrix can be created with a list or tuple of 16 values.
        If no values are provided, an "identity matrix" will be created
        (1.0 on the main diagonal). Matrix objects are immutable, so
        all operations return a new Mat4 object.

        :Parameters:
            `values` : tuple of float or int
                A tuple or list containing 16 floats or ints.
        """

        new = super().__new__(Mat4, values)
        assert len(new) == 16, "A 4x4 Matrix requires 16 values"
        return new

    @classmethod
    def orthogonal_projection(
        cls: type[Mat4T],
        left: float,
        right: float,
        bottom: float,
        top: float,
        z_near: float,
        z_far: float
    ) -> Mat4T:
        """Create a Mat4 orthographic projection matrix for use with OpenGL.

        This matrix doesn't actually perform the projection; it transforms the
        space so that OpenGL's vertex processing performs it.
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
    def perspective_projection(
        cls: type[Mat4T],
        aspect: float,
        z_near: float,
        z_far: float,
        fov: float = 60
    ) -> Mat4T:
        """
        Create a Mat4 perspective projection matrix for use with OpenGL.

        This matrix doesn't actually perform the projection; it transforms the
        space so that OpenGL's vertex processing performs it.

        :Parameters:
            `aspect` : The aspect ratio as a `float`
            `z_near` : The near plane as a `float`
            `z_far` : The far plane as a `float`
            `fov` : Field of view in degrees as a `float`
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
        """Create a rotation matrix from an angle and Vec3.

        :Parameters:
            `angle` : A `float` :
                The angle as a float.
            `vector` : A `Vec3`, or 3 component tuple of float or int :
                Vec3 or tuple with x, y and z translation values
        """
        return cls().rotate(angle, vector)

    @classmethod
    def from_scale(cls: type[Mat4T], vector: Vec3) -> Mat4T:
        """Create a scale matrix from a Vec3.

        :Parameters:
            `vector` : A `Vec3`, or 3 component tuple of float or int
                Vec3 or tuple with x, y and z scale values
        """
        return cls((vector[0], 0.0, 0.0, 0.0,
                    0.0, vector[1], 0.0, 0.0,
                    0.0, 0.0, vector[2], 0.0,
                    0.0, 0.0, 0.0, 1.0))

    @classmethod
    def from_translation(cls: type[Mat4T], vector: Vec3) -> Mat4T:
        """Create a translation matrix from a Vec3.

        :Parameters:
            `vector` : A `Vec3`, or 3 component tuple of float or int
                Vec3 or tuple with x, y and z translation values
        """
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
            return Vec4(sum(map(_mul, r0, other)),
                        sum(map(_mul, r1, other)),
                        sum(map(_mul, r2, other)),
                        sum(map(_mul, r3, other)))

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
        return Mat4((sum(map(_mul, c0, r0)), sum(map(_mul, c0, r1)), sum(map(_mul, c0, r2)), sum(map(_mul, c0, r3)),
                     sum(map(_mul, c1, r0)), sum(map(_mul, c1, r1)), sum(map(_mul, c1, r2)), sum(map(_mul, c1, r3)),
                     sum(map(_mul, c2, r0)), sum(map(_mul, c2, r1)), sum(map(_mul, c2, r2)), sum(map(_mul, c2, r3)),
                     sum(map(_mul, c3, r0)), sum(map(_mul, c3, r1)), sum(map(_mul, c3, r2)), sum(map(_mul, c3, r3))))

    # def __getitem__(self, item):
    #     row = [slice(0, 4), slice(4, 8), slice(8, 12), slice(12, 16)][item]
    #     return super().__getitem__(row)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self[0:4]}\n    {self[4:8]}\n    {self[8:12]}\n    {self[12:16]}"
