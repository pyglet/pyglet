# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2020 pyglet contributors
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

"""Matrix operations.

This module provides a convenient :py:class:`~pyglet.matrix.Mat4` class for
representing 4x4 matricies. Helper functions for creating, rotating, scaling,
and transforming these matrices are also provided. The internal datatype of
:py:class:`~pyglet.matrix.Mat4` is a 1-dimensional array, so instances can
be passed directly to OpenGL.

"""

import math as _math
import operator as _operator
import warnings as _warnings


def create_orthogonal(left, right, bottom, top, znear, zfar):
    """Create a Mat4 orthographic projection matrix."""
    width = right - left
    height = top - bottom
    depth = zfar - znear

    sx = 2.0 / width
    sy = 2.0 / height
    sz = 2.0 / -depth

    tx = -(right + left) / width
    ty = -(top + bottom) / height
    tz = -(zfar + znear) / depth

    return Mat4((sx, 0.0, 0.0, 0.0,
                 0.0, sy, 0.0, 0.0,
                 0.0, 0.0, sz, 0.0,
                 tx, ty, tz, 1.0))


def create_perspective(left, right, bottom, top, znear, zfar, fov=60):
    """Create a Mat4 perspective projection matrix."""
    width = right - left
    height = top - bottom
    aspect = width / height

    xymax = znear * _math.tan(fov * _math.pi / 360)
    ymin = -xymax
    xmin = -xymax

    width = xymax - xmin
    height = xymax - ymin
    depth = zfar - znear
    q = -(zfar + znear) / depth
    qn = -2 * zfar * znear / depth

    w = 2 * znear / width
    w = w / aspect
    h = 2 * znear / height

    return Mat4((w, 0, 0, 0,
                 0, h, 0, 0,
                 0, 0, q, -1,
                 0, 0, qn, 0))


class Mat4(tuple):
    """A 4x4 Matrix

    `Mat4` is a simple immutable 4x4 Matrix, with a few operators.
    Two types of multiplication are possible. The "*" operator
    will perform elementwise multiplication, wheras the "@"
    operator will perform Matrix multiplication. Internally,
    data is stored in a linear 1D array, allowing direct passing
    to OpenGL.
    """

    def __new__(cls, values=None):
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
        values = values or (1.0, 0.0, 0.0, 0.0,
                            0.0, 1.0, 0.0, 0.0,
                            0.0, 0.0, 1.0, 0.0,
                            0.0, 0.0, 0.0, 1.0)
        return super().__new__(Mat4, values)

    def row(self, index):
        """Get a specific row as a tuple."""
        return self[index*4:index*4+4]

    def column(self, index):
        """Get a specific column as a tuple."""
        return self[index::4]

    def scale(self, x=1, y=1, z=1):
        """Get a scale Matrix on x, y, or z axis."""
        temp = list(self)
        temp[0] *= x
        temp[5] *= y
        temp[10] *= z
        return Mat4(temp)

    def translate(self, x=0, y=0, z=0):
        """Get a translate Matrix along x, y, and z axis."""
        return Mat4(self) @ Mat4((1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1))

    def rotate(self, angle=0, x=0, y=0, z=0):
        """Get a rotation Matrix on x, y, or z axis."""
        assert all(abs(n) <= 1 for n in (x, y, z)), "x,y,z must be normalized (<=1)"
        c = _math.cos(angle)
        s = _math.sin(angle)
        t = 1 - c
        tempx, tempy, tempz = t * x, t * y, t * z

        ra = c + tempx * x
        rb = 0 + tempx * y + s * z
        rc = 0 + tempx * z - s * y
        re = 0 + tempy * x - s * z
        rf = c + tempy * y
        rg = 0 + tempy * z + s * x
        ri = 0 + tempz * x + s * y
        rj = 0 + tempz * y - s * x
        rk = c + tempz * z

        # ra, rb, rc, --
        # re, rf, rg, --
        # ri, rj, rk, --
        # --, --, --, --

        return Mat4(self) @ Mat4((ra, rb, rc, 0, re, rf, rg, 0, ri, rj, rk, 0, 0, 0, 0, 1))

    def transpose(self):
        """Get a tranpose of this Matrix."""
        return Mat4(self[0::4] + self[1::4] + self[2::4] + self[3::4])

    def __add__(self, other):
        assert len(other) == 16, "Can only add to other Mat4 types"
        return Mat4(tuple(s + o for s, o in zip(self, other)))

    def __sub__(self, other):
        assert len(other) == 16, "Can only subtract from other Mat4 types"
        return Mat4(tuple(s - o for s, o in zip(self, other)))

    def __pos__(self):
        return self

    def __neg__(self):
        return Mat4(tuple(-v for v in self))

    def __invert__(self):
        mat = list(self)
        a = mat[10] * mat[15] - mat[11] * mat[14]
        b = mat[9] * mat[15] - mat[11] * mat[13]
        c = mat[9] * mat[14] - mat[10] * mat[13]
        d = mat[8] * mat[15] - mat[11] * mat[12]
        e = mat[8] * mat[14] - mat[10] * mat[12]
        f = mat[8] * mat[13] - mat[9] * mat[12]
        g = mat[6] * mat[15] - mat[7] * mat[14]
        h = mat[5] * mat[15] - mat[7] * mat[13]
        i = mat[5] * mat[14] - mat[6] * mat[13]
        j = mat[6] * mat[11] - mat[7] * mat[10]
        k = mat[5] * mat[11] - mat[7] * mat[9]
        l = mat[5] * mat[10] - mat[6] * mat[9]
        m = mat[4] * mat[15] - mat[7] * mat[12]
        n = mat[4] * mat[14] - mat[6] * mat[12]
        o = mat[4] * mat[11] - mat[7] * mat[8]
        p = mat[4] * mat[10] - mat[6] * mat[8]
        q = mat[4] * mat[13] - mat[5] * mat[12]
        r = mat[4] * mat[9] - mat[5] * mat[8]

        det = (mat[0] * (mat[5] * a - mat[6] * b + mat[7] * c)
               - mat[1] * (mat[4] * a - mat[6] * d + mat[7] * e)
               + mat[2] * (mat[4] * b - mat[5] * d + mat[7] * f)
               - mat[3] * (mat[4] * c - mat[5] * e + mat[6] * f))

        if det == 0:
            _warnings.warn("Unable to calculate inverse of singular Matrix")
            return self

        pdet = 1 / det
        ndet = -pdet

        return Mat4((pdet * (mat[5] * a - mat[6] * b + mat[7] * c),
                     ndet * (mat[1] * a - mat[2] * b + mat[3] * c),
                     pdet * (mat[1] * g - mat[2] * h + mat[3] * i),
                     ndet * (mat[1] * j - mat[2] * k + mat[3] * l),
                     ndet * (mat[4] * a - mat[6] * d + mat[7] * e),
                     pdet * (mat[0] * a - mat[2] * d + mat[3] * e),
                     ndet * (mat[0] * g - mat[2] * m + mat[3] * n),
                     pdet * (mat[0] * j - mat[2] * o + mat[3] * p),
                     pdet * (mat[4] * b - mat[5] * d + mat[7] * f),
                     ndet * (mat[0] * b - mat[1] * d + mat[3] * f),
                     pdet * (mat[0] * h - mat[1] * m + mat[3] * q),
                     ndet * (mat[0] * k - mat[1] * o + mat[3] * r),
                     ndet * (mat[4] * c - mat[5] * e + mat[6] * f),
                     pdet * (mat[0] * c - mat[1] * e + mat[2] * f),
                     ndet * (mat[0] * i - mat[1] * n + mat[2] * q),
                     pdet * (mat[0] * l - mat[1] * p + mat[2] * r)))

    def __round__(self, n=None):
        return Mat4(tuple(round(v, n) for v in self))

    def __mul__(self, other):
        raise NotImplementedError("Please use the @ operator for Matrix multiplication.")

    def __matmul__(self, other):
        assert len(other) == 16, "Can only multiply with other Mat4 types"
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

        # Multiply and sum rows * colums:
        a = sum(map(_operator.mul, r0, c0))
        b = sum(map(_operator.mul, r0, c1))
        c = sum(map(_operator.mul, r0, c2))
        d = sum(map(_operator.mul, r0, c3))
        e = sum(map(_operator.mul, r1, c0))
        f = sum(map(_operator.mul, r1, c1))
        g = sum(map(_operator.mul, r1, c2))
        h = sum(map(_operator.mul, r1, c3))
        i = sum(map(_operator.mul, r2, c0))
        j = sum(map(_operator.mul, r2, c1))
        k = sum(map(_operator.mul, r2, c2))
        l = sum(map(_operator.mul, r2, c3))
        m = sum(map(_operator.mul, r3, c0))
        n = sum(map(_operator.mul, r3, c1))
        o = sum(map(_operator.mul, r3, c2))
        p = sum(map(_operator.mul, r3, c3))

        return Mat4((a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p))

    def __repr__(self):
        return f"{self.__class__.__name__}{self[0:4]}\n    {self[4:8]}\n    {self[8:12]}\n    {self[12:16]}"
