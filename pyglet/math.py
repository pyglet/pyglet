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


def clamp(num: float, minimum: float, maximum: float) -> float:
    """Clamp a value between a minimum and maximum limit."""
    return max(min(num, maximum), minimum)


class Vec2(_typing.NamedTuple):
    """A two-dimensional vector represented as an X Y coordinate pair.

    `Vec2` is an immutable 2D Vector, including most common
    operators. As an immutable type, all operations return a new object.

    .. note:: The Python `len` operator returns the number of elements in
              the vector. For the vector length, use the `abs` operator.
    """
    x: float = 0.0
    y: float = 0.0

    __match_args__ = 'x', 'y'

    def __add__(self, other: Vec2 | tuple[float, float] | float) -> Vec2:
        try:
            return Vec2(self[0] + other[0], self.y + other[1])
        except TypeError:
            return Vec2(self[0] + other, self[1] + other)

    def __radd__(self, other: Vec2 | tuple[float, float] | float) -> Vec2:
        try:
            return self.__add__(other)
        except TypeError as err:
            if other == 0:  # Required for functionality with sum()
                return self
            raise err

    def __sub__(self, other: Vec2 | tuple[float, float] | float) -> Vec2:
        try:
            return Vec2(self[0] - other[0], self[1] - other[1])
        except TypeError:
            return Vec2(self[0] - other, self[1] - other)

    def __rsub__(self, other: Vec2 | tuple[float, float] | float) -> Vec2:
        try:
            return Vec2(other[0] - self[0], other[1] - self[1])
        except TypeError:
            return Vec2(other - self[0], other - self[1])

    def __mul__(self, scalar: Vec2 | float | tuple[float, float]) -> Vec2:
        try:
            return Vec2(self[0] * scalar[0], self[1] * scalar[1])
        except TypeError:
            return Vec2(self[0] * scalar, self[1] * scalar)

    def __truediv__(self, scalar: Vec2 | float | tuple[float, float]) -> Vec2:
        try:
            return Vec2(self[0] / scalar[0], self[1] / scalar[1])
        except TypeError:
            return Vec2(self[0] / scalar, self[1] / scalar)

    def __rtruediv__(self, scalar: Vec2 | float | tuple[float, float]) -> Vec2:
        try:
            return Vec2(scalar[0] / self[0], scalar[1] / self[1])
        except TypeError:
            return Vec2(scalar / self[0], scalar / self[1])

    def __floordiv__(self, scalar: Vec2 | float | tuple[float, float]) -> Vec2:
        try:
            return Vec2(self.x // scalar[0], self.y // scalar[1])
        except TypeError:
            return Vec2(self[0] // scalar, self[1] // scalar)

    def __rfloordiv__(self, scalar: Vec2 | float | tuple[float, float]) -> Vec2:
        try:
            return Vec2(scalar[0] // self[0], scalar[1] // self[1])
        except TypeError:
            return Vec2(scalar // self[0], scalar // self[1])

    __rmul__ = __mul__  # Order doesn't matter here so we can use __mul__

    def __abs__(self) -> Vec2:
        return Vec2(abs(self[0]), abs(self[1]))

    def __neg__(self) -> Vec2:
        return Vec2(-self[0], -self[1])

    def __round__(self, ndigits: _typing.Optional[int] = None) -> Vec2:
        return Vec2(*(round(v, ndigits) for v in self))

    def __lt__(self, other: Vec2 | tuple[float, float]) -> bool:
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
    def from_polar(mag: float, angle: float) -> Vec2:
        """Create a new vector from the given polar coordinates.

        Args:
          mag: The desired magnitude.
          angle: The angle, in radians.
        """
        return Vec2(mag * _math.cos(angle), mag * _math.sin(angle))

    @property
    def length(self) -> float:
        """Get the length of the vector: ``sqrt(x ** 2 + y ** 2)``
        """
        return _math.sqrt(self[0] ** 2 + self[1] ** 2)

    @property
    def heading(self) -> float:
        """The heading of the vector in radians.

        Shortcut for `atan2(y, x)` meaning it returns a value between
        -pi and pi. ``Vec2(1, 0)`` will have a heading of 0. Counter-clockwise
        is positive moving towards pi, and clockwise is negative moving towards -pi.
        """
        return _math.atan2(self[1], self[0])

    @property
    def length_squared(self) -> float:
        """Get the squared length of the vector.

        This is simply shortcut for `x ** 2 + y ** 2` and can be used
        for faster comparisons without the need for a square root.
        """
        return self[0] ** 2.0 + self[1] ** 2.0

    def lerp(self, other: tuple[float, float], amount: float) -> Vec2:
        """Create a new Vec2 linearly interpolated between this vector and another Vec2.

        The equivalent in GLSL is `mix`.

        Args:
          other: Another Vec2 instance.
          amount: The amount of interpolation between this vector, and the other
                  vector. This should be a value between 0.0 and 1.0. For example:
                  0.5 is the midway point between both vectors.
        """
        return Vec2(self[0] + (amount * (other[0] - self.x)),
                    self[1] + (amount * (other[1] - self.y)))

    def step(self, edge: tuple[float, float]) -> Vec2:
        """A step function that returns 0.0 for a component if it is less than the edge, and 1.0 otherwise.

        This can be used enable and disable some behavior based on a condition.

        Example::

            # First component is less than 1.0, second component is greater than 1.0
            >>> Vec2(0.5, 1.5).step((1.0, 1.0))
            Vec2(1.0, 0.0)

        Args:
            edge: A Vec2 instance.
        """
        return Vec2(0.0 if self[0] < edge[0] else 1.0,
                    0.0 if self[1] < edge[1] else 1.0)

    def reflect(self, vector: Vec2) -> Vec2:
        """Create a new Vec2 reflected (ricochet) from the given normalized vector.

        Args:
          vector: A normalized vector.
        """
        return self - vector * 2 * vector.dot(self)

    def rotate(self, angle: float) -> Vec2:
        """Create a new vector rotated by the angle. The length remains unchanged.

        Args:
          angle: The desired angle, in radians.
        """
        s = _math.sin(angle)
        c = _math.cos(angle)
        return Vec2(c * self[0] - s * self[1], s * self[0] + c * self[1])

    def distance(self, other: tuple[int, int]) -> float:
        """Calculate the distance between this vector and another vector."""
        return _math.sqrt(((other[0] - self[0]) ** 2) + ((other[1] - self[1]) ** 2))

    def normalize(self) -> Vec2:
        """Normalize the vector to have a length of 1.0. i.e. make it a unit vector."""
        d = _math.sqrt(self[0] ** 2 + self[1] ** 2)
        if d:
            return Vec2(self[0] / d, self[1] / d)
        return self

    def clamp(self, min_val: float, max_val: float) -> Vec2:
        """Restrict the value of the X and Y components of the vector to be within the given values."""
        return Vec2(clamp(self.x, min_val, max_val), clamp(self.y, min_val, max_val))

    def dot(self, other: tuple[float, float]) -> float:
        """Calculate the dot product of this vector and another 2D vector."""
        return self[0] * other[0] + self[1] * other[1]

    def index(self, *args):
        raise NotImplementedError("Vec types can be indexed directly.")

    def __getattr__(self, attrs: str) -> _typing.Union[Vec2, Vec3, Vec4]:
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}.get(len(attrs))
            return vec_class(*(self['xy'.index(c)] for c in attrs))
        except (ValueError, TypeError):
            raise AttributeError(f"'Vec2' has no attribute: '{attrs}'.")


class Vec3(_typing.NamedTuple):
    """A three-dimensional vector represented as X Y Z coordinates.

    `Vec3` is an immutable 2D Vector, including most common operators.
    As an immutable type, all operations return a new object.

    .. note:: The Python `len` operator returns the number of elements in
              the vector. For the vector length, use the `abs` operator.
    """
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    __match_args__ = 'x', 'y', 'z'

    @property
    def mag(self) -> float:
        """The magnitude, or length of the vector.

        The distance between the coordinates and the origin.
        Alias of abs(vector_instance).
        """
        return self.__abs__()

    def __add__(self, other: Vec3 | tuple[int, int] | float) -> Vec3:
        try:
            return Vec3(self[0] + other[0], self[1] + other[1], self[2] + other[2])
        except TypeError:
            return Vec3(self[0] + other, self[1] + other, self[2] + other)

    def __sub__(self, other: Vec3 | tuple[int, int] | float) -> Vec3:
        try:
            return Vec3(self[0] - other[0], self[1] - other[1], self[2] - other[2])
        except TypeError:
            return Vec3(self[0] - other, self[1] - other, self[2] - other)

    def __rsub__(self, other: Vec3 | tuple[int, int] | float) -> Vec3:
        try:
            return Vec3(other[0] - self[0], other[1] - self[1], other[2] - self[2])
        except TypeError:
            return Vec3(other - self[0], other - self[1], other - self[2])  

    def __mul__(self, scalar: float | tuple[float, float, float]) -> Vec3:
        try:
            return Vec3(self[0] * scalar[0], self[1] * scalar[1], self[2] * scalar[2])
        except TypeError:
            return Vec3(self[0] * scalar, self[1] * scalar, self[2] * scalar)

    def __truediv__(self, scalar: float | tuple[float, float, float]) -> Vec3:
        try:
            return Vec3(self[0] / scalar[0], self[1] / scalar[1], self[2] / scalar[2])
        except TypeError:
            return Vec3(self[0] / scalar, self[1] / scalar, self[2] / scalar)

    def __rtruediv__(self, scalar: float | tuple[float, float, float]) -> Vec3: 
        try:
            return Vec3(scalar[0] / self[0], scalar[1] / self[1], scalar[2] / self[2])
        except TypeError:
            return Vec3(scalar / self[0], scalar / self[1], scalar / self[2])

    def __floordiv__(self, scalar: float | tuple[float, float, float]) -> Vec3:
        try:
            return Vec3(self[0] // scalar[0], self[1] // scalar[1], self[2] // scalar[2])
        except TypeError:
            return Vec3(self[0] // scalar, self[1] // scalar, self[2] // scalar)

    def __rfloordiv__(self, scalar: float | tuple[float, float, float]) -> Vec3:
        try:
            return Vec3(scalar[0] // self[0], scalar[1] // self[1], scalar[2] // self[2])
        except TypeError:
            return Vec3(scalar // self[0], scalar // self[1], scalar // self[2])

    def __radd__(self, other: _typing.Union[Vec3, int]) -> Vec3:
        try:
            return self.__add__(_typing.cast(Vec3, other))
        except TypeError as err:
            if other == 0:  # Required for functionality with sum()
                return self
            raise err

    __rmul__ = __mul__

    def __abs__(self) -> Vec3:
        return Vec3(abs(self[0]), abs(self[1]), abs(self[2]))

    def __neg__(self) -> Vec3:
        return Vec3(-self[0], -self[1], -self[2])

    def __round__(self, ndigits: _typing.Optional[int] = None) -> Vec3:
        return Vec3(*(round(v, ndigits) for v in self))

    def __lt__(self, other: Vec3) -> bool:
        # TODO: Inline squared
        return self[0] ** 2 + self[1] ** 2 + self[2] ** 2 < other[0] ** 2 + other[1] ** 2 + other[2] ** 2

    @property
    def length(self) -> float:
        """Get the length of the vector: ``sqrt(x ** 2 + y ** 2 + z ** 2)``"""
        return _math.sqrt(self[0] ** 2 + self[1] ** 2 + self[2] ** 2)

    @property
    def length_squared(self) -> float:
        return self[0] ** 2 + self[1] ** 2 + self[2] ** 2

    def cross(self, other: Vec3) -> Vec3:
        """Calculate the cross product of this vector and another 3D vector."""
        return Vec3((self.y * other.z) - (self.z * other.y),
                    (self.z * other.x) - (self.x * other.z),
                    (self.x * other.y) - (self.y * other.x))

    def dot(self, other: Vec3) -> float:
        """Calculate the dot product of this vector and another 3D vector."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def lerp(self, other: Vec3, alpha: float) -> Vec3:
        """Create a new Vec3 linearly interpolated between this vector and another Vec3.

        Args:
          other: Another Vec3 instance.
          alpha: The amount of interpolation between this vector, and the other
                 vector. This should be a value between 0.0 and 1.0. For example:
                 0.5 is the midway point between both vectors.
        """
        return Vec3(self.x + (alpha * (other.x - self.x)),
                    self.y + (alpha * (other.y - self.y)),
                    self.z + (alpha * (other.z - self.z)))

    def distance(self, other: Vec3) -> float:
        """Get the distance between this vector and another 3D vector."""
        return _math.sqrt(((other.x - self.x) ** 2) +
                          ((other.y - self.y) ** 2) +
                          ((other.z - self.z) ** 2))

    def normalize(self) -> Vec3:
        """Normalize the vector to have a magnitude of 1. i.e. make it a unit vector."""
        try:
            d = self.length()
            return Vec3(self.x / d, self.y / d, self.z / d)
        except ZeroDivisionError:
            return self

    def clamp(self, min_val: float, max_val: float) -> Vec3:
        """Restrict the value of the X, Y and Z components of the vector to be within the given values."""
        return Vec3(clamp(self.x, min_val, max_val),
                    clamp(self.y, min_val, max_val),
                    clamp(self.z, min_val, max_val))

    def index(self, *args):
        raise NotImplementedError("Vec types can be indexed directly.")

    def __getattr__(self, attrs: str) -> _typing.Union[Vec2, Vec3, Vec4]:
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}.get(len(attrs))
            return vec_class(*(self['xyz'.index(c)] for c in attrs))
        except (ValueError, TypeError):
            raise AttributeError(f"'Vec3' has no attribute: '{attrs}'.")


class Vec4(_typing.NamedTuple):
    """A four-dimensional vector represented as X Y Z W coordinates.

    `Vec4` is an immutable 2D Vector, including most common operators.
    As an immutable type, all operations return a new object.

    .. note:: The Python `len` operator returns the number of elements in
              the vector. For the vector length, use the `abs` operator.
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 0.0

    __match_args__ = 'x', 'y', 'z', 'w'

    def __add__(self, other: Vec4) -> Vec4:
        return Vec4(self.x + other.x, self.y + other.y, self.z + other.z, self.w + other.w)

    def __sub__(self, other: Vec4) -> Vec4:
        return Vec4(self.x - other.x, self.y - other.y, self.z - other.z, self.w - other.w)

    def __mul__(self, scalar: float | tuple[float, float, float, float]) -> Vec4:
        try:
            return Vec4(self.x * scalar, self.y * scalar, self.z * scalar, self.w * scalar)
        except TypeError:
            return Vec4(self.x * scalar[0], self.y * scalar[1], self.z * scalar[2], self.w * scalar[3])

    def __truediv__(self, scalar: float | tuple[float, float, float, float]) -> Vec4:
        try:
            return Vec4(self.x / scalar, self.y / scalar, self.z / scalar, self.w / scalar)
        except TypeError:
            return Vec4(self.x / scalar[0], self.y / scalar[1], self.z / scalar[2], self.w / scalar[3])

    def __floordiv__(self, scalar: float | tuple[float, float, float, float]) -> Vec4:
        try:
            return Vec4(self.x // scalar, self.y // scalar, self.z // scalar, self.w // scalar)
        except TypeError:
            return Vec4(self.x // scalar[0], self.y // scalar[1], self.z // scalar[2], self.w // scalar[3])

    def __abs__(self) -> float:
        return _math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2 + self.w ** 2)

    def __neg__(self) -> Vec4:
        return Vec4(-self.x, -self.y, -self.z, -self.w)

    def __round__(self, ndigits: _typing.Optional[int] = None) -> Vec4:
        return Vec4(*(round(v, ndigits) for v in self))

    def __radd__(self, other: _typing.Union[Vec4, int]) -> Vec4:
        try:
            return self.__add__(_typing.cast(Vec4, other))
        except TypeError as err:
            if other == 0:  # Required for functionality with sum()
                return self
            raise err

    __rsub__ = __sub__
    __rmul__ = __mul__
    __rtruediv__ = __truediv__
    __rfloordiv__ = __floordiv__

    def __lt__(self, other: Vec4) -> bool:
        return abs(self) < abs(other)

    def lerp(self, other: Vec4, alpha: float) -> Vec4:
        """Create a new Vec4 linearly interpolated between this vector and another Vec4.

        Args:
          other: Another Vec4 instance.
          alpha: The amount of interpolation between this vector, and the other
                 vector. This should be a value between 0.0 and 1.0. For example:
                 0.5 is the midway point between both vectors.
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

    def index(self, *args):
        raise NotImplemented("Vec types can be indexed directly.")

    def __getattr__(self, attrs: str) -> _typing.Union[Vec2, Vec3, Vec4]:
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}.get(len(attrs))
            return vec_class(*(self['xyzw'.index(c)] for c in attrs))
        except (ValueError, TypeError):
            raise AttributeError(f"'Vec4' has no attribute: '{attrs}'.")


class Mat3(tuple):
    """A 3x3 Matrix.

    `Mat3` is an immutable 3x3 Matrix, wich includes most common operators.

    A Matrix can be created with a list or tuple of 9 values.
    If no values are provided, an "identity matrix" will be created
    (1.0 on the main diagonal). Because Mat3 objects are immutable,
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

    def __invert__(self) -> Mat3:
        # extract the elements in row-column form. (matrix is stored column first)
        a11, a12, a13, a21, a22, a23, a31, a32, a33 = self

        # Calculate Adj(self) values column-row order
        # | a d g |
        # | b e h |
        # | c f i |
        a = a22 * a33 - a32 * a23 # +
        b = a31 * a23 - a21 * a33 # -
        c = a21 * a32 - a22 * a31 # +
        d = a32 * a13 - a12 * a33 # -
        e = a11 * a33 - a31 * a13 # +
        f = a31 * a12 - a11 * a32 # -
        g = a12 * a23 - a22 * a13 # +
        h = a21 * a13 - a11 * a23 # -
        i = a11 * a22 - a21 * a12 # +

        # Calculate determinant
        det = a11 * a + a21 * d + a31 * g

        if det == 0:
            _warnings.warn("Unable to calculate inverse of singular Matrix")
            return self

        # get determinant reciprocal
        rep = 1.0 / det

        # get inverse: A^-1 = def(A)^-1 * adj(A)
        return Mat3((
            a * rep, b * rep, c * rep,
            d * rep, e * rep, f * rep,
            g * rep, h * rep, i * rep,
        ))


    def __round__(self, ndigits: _typing.Optional[int] = None) -> Mat3:
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
            x, y, z = other
            # extract the elements in row-column form. (matrix is stored column first)
            a11, a12, a13, a21, a22, a23, a31, a32, a33 = self
            return Vec3(
                a11 * x + a21 * y + a31 * z,
                a12 * x + a22 * y + a32 * z,
                a13 * x + a23 * y + a33 * z,
            )

        if not isinstance(other, Mat3):
            raise TypeError("Can only multiply with Mat3 or Vec3 types")

        # extract the elements in row-column form. (matrix is stored column first)
        a11, a12, a13, a21, a22, a23, a31, a32, a33 = self
        b11, b12, b13, b21, b22, b23, b31, b32, b33 = other

        # Multiply and sum rows * columns :~}
        return Mat3((
            # Column 1
            a11 * b11 + a21 * b12 + a31 * b13, a12 * b11 + a22 * b12 + a32 * b13, a13 * b11 + a23 * b12 + a33 * b13,
            # Column 2
            a11 * b21 + a21 * b22 + a31 * b23, a12 * b21 + a22 * b22 + a32 * b23, a13 * b21 + a23 * b22 + a33 * b23,
            # Column 3
            a11 * b31 + a21 * b32 + a31 * b33, a12 * b31 + a22 * b32 + a32 * b33, a13 * b31 + a23 * b32 + a33 * b33,
        ))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self[0:3]}\n    {self[3:6]}\n    {self[6:9]}"


class Mat4(tuple):
    """A 4x4 Matrix.

    `Mat4` is an immutable 4x4 Matrix, which includs most common operators.
    This includes class methods for creating orthogonal and perspective
    projection matrixes, which can be used directly by OpenGL.

    A Matrix can be created with a list or tuple of 16 values. If no values
    are provided, an "identity matrix" will be created (1.0 on the main diagonal).
    Mat4 objects are immutable, so all operations return a new Mat4 object.

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
        """Create a rotation matrix from an angle and Vec3.

        Args:
          angle: The desired angle, in radians.
          vector: A Vec3 indicating the direction.
        """
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

        det = (a11 * (a22 * a - a23 * b + a24 * c)
               - a12 * (a21 * a - a23 * d + a24 * e)
               + a13 * (a21 * b - a22 * d + a24 * f)
               - a14 * (a21 * c - a22 * e + a23 * f))

        if det == 0:
            _warnings.warn("Unable to calculate inverse of singular Matrix")
            return self

        pdet = 1 / det
        ndet = -pdet

        return Mat4((pdet * (a22 * a - a23 * b + a24 * c),
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
                     pdet * (a11 * l - a12 * p + a13 * r)))

    def __round__(self, ndigits: _typing.Optional[int] = None) -> Mat4:
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
            raise TypeError("Can only multiply with Mat4 or Vec4 types")

        # extract the elements in row-column form. (matrix is stored column first)
        a11, a12, a13, a14, a21, a22, a23, a24, a31, a32, a33, a34, a41, a42, a43, a44 = self
        b11, b12, b13, b14, b21, b22, b23, b24, b31, b32, b33, b34, b41, b42, b43, b44 = other
        # Multiply and sum rows * columns:
        return Mat4((
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
        ))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self[0:4]}\n    {self[4:8]}\n    {self[8:12]}\n    {self[12:16]}"


class Quaternion(_typing.NamedTuple):
    """Quaternion"""

    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

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
    def mag(self) -> float:
        """The magnitude, or length, of the Quaternion.

        The distance between the coordinates and the origin.
        Alias of abs(quaternion_instance).
        """
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
        return Quaternion(self.w / m, self.x / m, self.y / m, self.z / m)

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
        a, u = self.w, Vec3(*self[1:])
        b, v = other.w, Vec3(*other[1:])
        scalar = a * b - u.dot(v)
        vector = v * a + u * b + u.cross(v)
        return Quaternion(scalar, *vector)
