# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2022 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

"""Matrix and Vector math.

This module provides Vector and Matrix objects, including Vec2, Vec3,
Vec4, Mat3, and Mat4. Most common matrix and vector operations are
supported. Helper methods are included for rotating, scaling, and
transforming. The :py:class:`~pyglet.matrix.Mat4` includes class methods
for creating orthographic and perspective projection matrixes.

:note: For performance, Matrixes subclass the `tuple` type. They
    are therefore immutable - all operations return a new object;
    the object is not updated in-place.
"""

import math as _math
import warnings as _warnings

from operator import mul as _mul


def clamp(num, min_val, max_val):
    return max(min(num, max_val), min_val)


class Vec2:

    __slots__ = 'x', 'y'

    """A two-dimensional vector represented as an X Y coordinate pair.

    :parameters: 
        `x` : int or float : 
            The X coordinate of the vector.
        `y`   : int or float :
            The Y coordinate of the vector.

    """

    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __iter__(self):
        yield self.x
        yield self.y

    def __len__(self):
        return 2

    def __getitem__(self, item):
        return (self.x, self.y)[item]

    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vec2(self.x * other.x, self.y * other.y)

    def __truediv__(self, other):
        return Vec2(self.x / other.x, self.y / other.y)

    def __abs__(self):
        return _math.sqrt(self.x ** 2 + self.y ** 2)

    def __neg__(self):
        return Vec2(-self.x, -self.y)

    def __round__(self, ndigits=None):
        return Vec2(*(round(v, ndigits) for v in self))

    def __radd__(self, other):
        """Reverse add. Required for functionality with sum()
        """
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y

    @staticmethod
    def from_polar(mag, angle):
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

    def from_magnitude(self, magnitude):
        """Create a new Vector of the given magnitude by normalizing,
        then scaling the vector. The heading remains unchanged.

        :parameters: 
            `magnitude` : int or float : 
                The magnitude of the new vector.

        :returns: A new vector with the magnitude.
        :rtype: Vec2
        """
        return self.normalize().scale(magnitude)

    def from_heading(self, heading):
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
    def heading(self):
        """The angle of the vector in radians.

        :type: float
        """
        return _math.atan2(self.y, self.x)

    @property
    def mag(self):
        """The magnitude, or length of the vector. The distance between the coordinates and the origin.

        Alias of abs(self).

        :type: float
        """
        return self.__abs__()

    def limit(self, maximum):
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
            
    def lerp(self, other, alpha):
        """Create a new vector lineraly interpolated between this vector and another vector.

        :parameters: 
            `other`  : Vec2 :
                The vector to be linerly interpolated to.
            `alpha` : float or int :
                The amount of interpolation.
                Some value between 0.0 (this vector) and 1.0 (other vector). 
                0.5 is halfway inbetween.
        
        :returns: A new interpolated vector.
        :rtype: Vec2
        """
        return Vec2(self.x + (alpha * (other.x - self.x)),
                    self.y + (alpha * (other.y - self.y)))

    def scale(self, value):
        """Multiply the vector by a scalar value.

        :parameters: 
            `value`  : int or float :
                The ammount to be scaled by

        :returns: A new vector scaled by the value.
        :rtype: Vec2
        """
        return Vec2(self.x * value, self.y * value)

    def rotate(self, angle):
        """Create a new Vector rotated by the angle. The magnitude remains unchanged.

        :parameters: 
            `angle` : int or float : 
                The angle to rotate by

        :returns: A new rotated vector of the same magnitude.
        :rtype: Vec2
        """
        mag = self.mag
        heading = self.heading
        return Vec2(mag * _math.cos(heading + angle), mag * _math.sin(heading+angle))

    def distance(self, other):
        """Calculate the distance between this vector and another 2D vector.
        
        :parameters:
            `other`  : Vec2 :
                The other vector 

        :returns: The distance between the two vectors.
        :rtype: float
        """
        return _math.sqrt(((other.x - self.x) ** 2) + ((other.y - self.y) ** 2))

    def normalize(self):
        """Normalize the vector to have a magnitude of 1. i.e. make it a unit vector.

        :returns: A unit vector with the same heading.
        :rtype: Vec2
        """
        d = self.__abs__()
        if d:
            return Vec2(self.x / d, self.y / d)
        return self

    def clamp(self, min_val, max_val):
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

    def dot(self, other):
        """Calculate the dot product of this vector and another 2D vector.

        :parameters: 
            `other`  : Vec2 :
                The other vector.
        
        :returns: The dot product of the two vectors.
        :rtype: float
        """
        return self.x * other.x + self.y * other.y

    def __getattr__(self, attrs):
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}.get(len(attrs))
            return vec_class(*(self['xy'.index(c)] for c in attrs))
        except Exception:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attrs}'")

    def __repr__(self):
        return f"Vec2({self.x}, {self.y})"


class Vec3:

    __slots__ = 'x', 'y', 'z'

    """A three-dimensional vector represented as X Y Z coordinates.

    :parameters: 
        `x` : int or float : 
            The X coordinate of the vector.
        `y`   : int or float :
            The Y coordinate of the vector.
        `z`   : int or float :
            The Z coordinate of the vector.

    """

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __getitem__(self, item):
        return (self.x, self.y, self.z)[item]

    def __len__(self):
        return 3

    @property
    def mag(self):
        """The magnitude, or length of the vector. The distance between the coordinates and the origin.

        Alias of abs(self).

        :type: float
        """
        return self.__abs__()

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        return Vec3(self.x * other.x, self.y * other.y, self.z * other.z)

    def __truediv__(self, other):
        return Vec3(self.x / other.x, self.y / other.y, self.z / other.z)

    def __abs__(self):
        return _math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def __round__(self, ndigits=None):
        return Vec3(*(round(v, ndigits) for v in self))

    def __radd__(self, other):
        """Reverse add. Required for functionality with sum()
        """
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y or self.z != other.z

    def from_magnitude(self, magnitude):
        """Create a new Vector of the given magnitude by normalizing,
        then scaling the vector. The rotation remains unchanged.

        :parameters: 
            `magnitude` : int or float : 
                The magnitude of the new vector.

        :returns: A new vector with the magnitude.
        :rtype: Vec3
        """
        return self.normalize().scale(magnitude)

    def limit(self, maximum):
        """Limit the magnitude of the vector to the value used for the max parameter.

        :parameters: 
            `maximum`  : int or float :
                The maximum magnitude for the vector.
        
        :returns: Either self or a new vector with the maximum magnitude.
        :rtype: Vec3
        """
        if self.x ** 2 + self.y ** 2 + self.z ** 2 > maximum * maximum * maximum:
            return self.from_magnitude(max)
        return self

    def cross(self, other):
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

    def dot(self, other):
        """Calculate the dot product of this vector and another 3D vector.

        :parameters:
            `other`  : Vec3 :
                The other vector.

        :returns: The dot product of the two vectors.
        :rtype: float
        """
        return self.x * other.x + self.y * other.y + self.z * other.z

    def lerp(self, other, alpha):
        """Create a new vector lineraly interpolated between this vector and another vector.

        :parameters: 
            `other`  : Vec3 :
                The vector to be linerly interpolated to.
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

    def scale(self, value):
        """Multiply the vector by a scalar value.

        :parameters: 
            `value`  : int or float :
                The ammount to be scaled by

        :returns: A new vector scaled by the value.
        :rtype: Vec3
        """
        return Vec3(self.x * value, self.y * value, self.z * value)

    def distance(self, other):
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

    def normalize(self):
        """Normalize the vector to have a magnitude of 1. i.e. make it a unit vector.

        :returns: A unit vector with the same rotation.
        :rtype: Vec3
        """
        d = self.__abs__()
        if d:
            return Vec3(self.x / d, self.y / d, self.z / d)
        return self

    def clamp(self, min_val, max_val):
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

    def __getattr__(self, attrs):
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}.get(len(attrs))
            return vec_class(*(self['xyz'.index(c)] for c in attrs))
        except Exception:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attrs}'")

    def __repr__(self):
        return f"Vec3({self.x}, {self.y}, {self.z})"


class Vec4:

    __slots__ = 'x', 'y', 'z', 'w'

    """A four-dimensional vector represented as X Y Z W coordinates.

    :parameters: 
        `x` : int or float : 
            The X coordinate of the vector.
        `y`   : int or float :
            The Y coordinate of the vector.
        `z`   : int or float :
            The Z coordinate of the vector.
        `w`   : int or float :
            The W coordinate of the vector.

    """

    def __init__(self, x=0.0, y=0.0, z=0.0, w=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z
        yield self.w

    def __getitem__(self, item):
        return (self.x, self.y, self.z, self.w)[item]

    def __len__(self):
        return 4

    def __add__(self, other):
        return Vec4(self.x + other.x, self.y + other.y, self.z + other.z, self.w + other.w)

    def __sub__(self, other):
        return Vec4(self.x - other.x, self.y - other.y, self.z - other.z, self.w - other.w)

    def __mul__(self, other):
        return Vec4(self.x * other.x, self.y * other.y, self.z * other.z, self.w * other.w)

    def __truediv__(self, other):
        return Vec4(self.x / other.x, self.y / other.y, self.z / other.z, self.w / other.w)

    def __abs__(self):
        return _math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2 + self.w ** 2)

    def __neg__(self):
        return Vec4(-self.x, -self.y, -self.z, -self.w)

    def __round__(self, ndigits=None):
        return Vec4(*(round(v, ndigits) for v in self))

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z and self.w == other.w

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y or self.z != other.z or self.w != other.w

    def lerp(self, other, alpha):
        return Vec4(self.x + (alpha * (other.x - self.x)),
                    self.y + (alpha * (other.y - self.y)),
                    self.z + (alpha * (other.z - self.z)),
                    self.w + (alpha * (other.w - self.w)))

    def scale(self, value):
        return Vec4(self.x * value, self.y * value, self.z * value, self.w * value)

    def distance(self, other):
        return _math.sqrt(((other.x - self.x) ** 2) +
                          ((other.y - self.y) ** 2) +
                          ((other.z - self.z) ** 2) +
                          ((other.w - self.w) ** 2))

    def normalize(self):
        d = self.__abs__()
        if d:
            return Vec4(self.x / d, self.y / d, self.z / d, self.w / d)
        return self

    def clamp(self, min_val, max_val):
        return Vec4(clamp(self.x, min_val, max_val),
                    clamp(self.y, min_val, max_val),
                    clamp(self.z, min_val, max_val),
                    clamp(self.w, min_val, max_val))

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z + self.w * other.w

    def __getattr__(self, attrs):
        try:
            # Allow swizzled getting of attrs
            vec_class = {2: Vec2, 3: Vec3, 4: Vec4}.get(len(attrs))
            return vec_class(*(self['xyzw'.index(c)] for c in attrs))
        except Exception:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attrs}'")

    def __repr__(self):
        return f"Vec4({self.x}, {self.y}, {self.z}, {self.w})"



class Mat3(tuple):
    """A 3x3 Matrix class

    `Mat3` is an immutable 3x3 Matrix, including most common
    operators. Matrix multiplication must be performed using
    the "@" operator.
    """

    def __new__(cls, values=None) -> 'Mat3':
        """Create a 3x3 Matrix

        A Mat3 can be created with a list or tuple of 9 values.
        If no values are provided, an "identity matrix" will be created
        (1.0 on the main diagonal). Matrix objects are immutable, so
        all operations return a new Mat3 object.

        :Parameters:
            `values` : tuple of float or int
                A tuple or list containing 9 floats or ints.
        """
        assert values is None or len(values) == 9, "A 3x3 Matrix requires 9 values"
        return super().__new__(Mat3, values or (1.0, 0.0, 0.0,
                                                0.0, 1.0, 0.0,
                                                0.0, 0.0, 1.0))

    def scale(self, sx: float, sy: float):
        return self @ (1.0 / sx, 0.0, 0.0, 0.0, 1.0 / sy, 0.0, 0.0, 0.0, 1.0)

    def translate(self, tx: float, ty: float):
        return self @ (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, -tx, ty, 1.0)

    def rotate(self, phi: float):
        s = _math.sin(_math.radians(phi))
        c = _math.cos(_math.radians(phi))
        return self @ (c, s, 0.0, -s, c, 0.0, 0.0, 0.0, 1.0)

    def shear(self, sx: float, sy: float):
        return self @ (1.0, sy, 0.0, sx, 1.0, 0.0, 0.0, 0.0, 1.0)

    def __add__(self, other) -> 'Mat3':
        assert len(other) == 9, "Can only add to other Mat3 types"
        return Mat3(tuple(s + o for s, o in zip(self, other)))

    def __sub__(self, other) -> 'Mat3':
        assert len(other) == 9, "Can only subtract from other Mat3 types"
        return Mat3(tuple(s - o for s, o in zip(self, other)))

    def __pos__(self):
        return self

    def __neg__(self) -> 'Mat3':
        return Mat3(tuple(-v for v in self))

    def __round__(self, ndigits=None) -> 'Mat3':
        return Mat3(tuple(round(v, ndigits) for v in self))

    def __mul__(self, other):
        raise NotImplementedError("Please use the @ operator for Matrix multiplication.")

    def __matmul__(self, other) -> 'Mat3' or 'Vec3':
        assert len(other) in (3, 9), "Can only multiply with Mat3 or Vec3 types"

        if type(other) is Vec3:
            # Columns:
            c0 = self[0::3]
            c1 = self[1::3]
            c2 = self[2::3]
            return Vec3(sum(map(_mul, c0, other)),
                        sum(map(_mul, c1, other)),
                        sum(map(_mul, c2, other)))

        # Rows:
        r0 = self[0:3]
        r1 = self[3:6]
        r2 = self[6:9]
        # Columns:
        c0 = other[0::3]
        c1 = other[1::3]
        c2 = other[2::3]

        # Multiply and sum rows * colums:
        return Mat3((sum(map(_mul, r0, c0)),
                     sum(map(_mul, r0, c1)),
                     sum(map(_mul, r0, c2)),

                     sum(map(_mul, r1, c0)),
                     sum(map(_mul, r1, c1)),
                     sum(map(_mul, r1, c2)),

                     sum(map(_mul, r2, c0)),
                     sum(map(_mul, r2, c1)),
                     sum(map(_mul, r2, c2))))

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

    def __new__(cls, values=None) -> 'Mat4':
        """Create a 4x4 Matrix

        A Matrix can be created with a list or tuple of 16 values.
        If no values are provided, an "identity matrix" will be created
        (1.0 on the main diagonal). Matrix objects are immutable, so
        all operations return a new Mat4 object.

        :Parameters:
            `values` : tuple of float or int
                A tuple or list containing 16 floats or ints.
        """
        assert values is None or len(values) == 16, "A 4x4 Matrix requires 16 values"
        return super().__new__(Mat4, values or (1.0, 0.0, 0.0, 0.0,
                                                0.0, 1.0, 0.0, 0.0,
                                                0.0, 0.0, 1.0, 0.0,
                                                0.0, 0.0, 0.0, 1.0))

    @classmethod
    def orthogonal_projection(cls, left, right, bottom, top, z_near, z_far) -> 'Mat4':
        """Create a Mat4 orthographic projection matrix."""
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
    def perspective_projection(cls, aspect, z_near, z_far, fov=60) -> 'Mat4':
        """
        Create a Mat4 perspective projection matrix.

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
    def from_translation(cls, vector: Vec3) -> 'Mat4':
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
    def from_rotation(cls, angle: float, vector: Vec3) -> 'Mat4':
        """Create a rotation matrix from an angle and Vec3.

        :Parameters:
            `angle` : A `float` :
                The angle as a float.
            `vector` : A `Vec3`, or 3 component tuple of float or int :
                Vec3 or tuple with x, y and z translation values
        """
        return cls().rotate(angle, vector)

    @classmethod
    def look_at_direction(cls, direction: Vec3, up: Vec3) -> 'Mat4':
        vec_z = direction.normalize()
        vec_x = direction.cross_product(up).normalize()
        vec_y = direction.cross_product(vec_z).normalize()

        return cls((vec_x.x, vec_y.x, vec_z.x, 0.0,
                    vec_x.y, vec_y.y, vec_z.y, 0.0,
                    vec_x.z, vec_z.z, vec_z.z, 0.0,
                    0.0, 0.0, 0.0, 1.0))

    @classmethod
    def look_at(cls, position: Vec3, target: Vec3, up: Vec3) -> 'Mat4':
        direction = target - position
        direction_mat4 = cls.look_at_direction(direction, up)
        position_mat4 = cls.from_translation(position.negate())
        return direction_mat4 @ position_mat4

    def row(self, index: int):
        """Get a specific row as a tuple."""
        return self[index*4:index*4+4]

    def column(self, index: int):
        """Get a specific column as a tuple."""
        return self[index::4]

    def scale(self, vector: Vec3) -> 'Mat4':
        """Get a scale Matrix on x, y, or z axis."""
        temp = list(self)
        temp[0] *= vector[0]
        temp[5] *= vector[1]
        temp[10] *= vector[2]
        return Mat4(temp)

    def translate(self, vector: Vec3) -> 'Mat4':
        """Get a translation Matrix along x, y, and z axis."""
        return Mat4(self) @ Mat4((1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, *vector, 1))

    def rotate(self, angle: float, vector: Vec3) -> 'Mat4':
        """Get a rotation Matrix on x, y, or z axis."""
        assert all(abs(n) <= 1 for n in vector), "vector must be normalized (<=1)"
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

    def transpose(self) -> 'Mat4':
        """Get a transpose of this Matrix."""
        return Mat4(self[0::4] + self[1::4] + self[2::4] + self[3::4])

    def __add__(self, other) -> 'Mat4':
        assert len(other) == 16, "Can only add to other Mat4 types"
        return Mat4(tuple(s + o for s, o in zip(self, other)))

    def __sub__(self, other) -> 'Mat4':
        assert len(other) == 16, "Can only subtract from other Mat4 types"
        return Mat4(tuple(s - o for s, o in zip(self, other)))

    def __pos__(self):
        return self

    def __neg__(self) -> 'Mat4':
        return Mat4(tuple(-v for v in self))

    def __invert__(self) -> 'Mat4':
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

    def __round__(self, ndigits=None) -> 'Mat4':
        return Mat4(tuple(round(v, ndigits) for v in self))

    def __mul__(self, other):
        raise NotImplementedError("Please use the @ operator for Matrix multiplication.")

    def __matmul__(self, other) -> 'Mat4' or 'Vec4':
        assert len(other) in (4, 16), "Can only multiply with Mat4 or Vec4 types"

        if type(other) is Vec4:
            # Columns:
            c0 = self[0::4]
            c1 = self[1::4]
            c2 = self[2::4]
            c3 = self[3::4]
            return Vec4(sum(map(_mul, c0, other)),
                        sum(map(_mul, c1, other)),
                        sum(map(_mul, c2, other)),
                        sum(map(_mul, c3, other)))

        # Rows:
        r0 = self[0:4]
        r1 = self[4:8]
        r2 = self[8:12]
        r3 = self[12:16]
        # Columns:
        c0 = other[0::4]
        c1 = other[1::4]
        c2 = other[2::4]
        c3 = other[3::4]

        # Multiply and sum rows * columns:
        return Mat4((sum(map(_mul, r0, c0)),
                     sum(map(_mul, r0, c1)),
                     sum(map(_mul, r0, c2)),
                     sum(map(_mul, r0, c3)),

                     sum(map(_mul, r1, c0)),
                     sum(map(_mul, r1, c1)),
                     sum(map(_mul, r1, c2)),
                     sum(map(_mul, r1, c3)),

                     sum(map(_mul, r2, c0)),
                     sum(map(_mul, r2, c1)),
                     sum(map(_mul, r2, c2)),
                     sum(map(_mul, r2, c3)),

                     sum(map(_mul, r3, c0)),
                     sum(map(_mul, r3, c1)),
                     sum(map(_mul, r3, c2)),
                     sum(map(_mul, r3, c3))))

    # def __getitem__(self, item):
    #     row = [slice(0, 4), slice(4, 8), slice(8, 12), slice(12, 16)][item]
    #     return super().__getitem__(row)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self[0:4]}\n    {self[4:8]}\n    {self[8:12]}\n    {self[12:16]}"
