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


def scale(matrix, x=1, y=1, z=1):
    """Scale a Matrix on x, y, or z axis."""
    temp = list(matrix)
    temp[0] *= x
    temp[5] *= y
    temp[10] *= z
    return Mat4(temp)


def translate(matrix, x=0, y=0, z=0):
    """Translate a Matrix along x, y, and z axis."""
    return Mat4(matrix) @ Mat4((1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1))


def rotate(matrix, angle=0, x=0, y=0, z=0):
    """Rotate a Matrix on x, y, or z axis."""
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

    return Mat4(matrix) @ Mat4((ra, rb, rc, 0, re, rf, rg, 0, ri, rj, rk, 0, 0, 0, 0, 1))


def transpose(matrix):
    """The transpose of a Matrix."""
    return Mat4(matrix[0::4] + matrix[1::4] + matrix[2::4] + matrix[3::4])


def inverse(matrix):
    """The inverse of a Matrix.

    Using Gauss-Jordan ekimination, the matrix supplied is transformed into
    the identity matrix using a sequence of elementary row operations (below).
    The same sequence of operations is applied to the identity matrix,
    transforming it into the supplied matrix's inverse.

    Elementary row operations:
        - multiply row by a scalar
        - swap two rows
        - add two rows together"""

    i = Mat4() # identity matrix

    # The pivot in each column is the element at Matrix[c, c] (diagonal elements).
    # The pivot row is the row containing the pivot element. Pivot elements must
    # be non-zero.
    # Any time matrix is changed, so is i.
    for c in range(4):
        # Find and swap pivot row into place
        if matrix[4*c + c] == 0:
            for r in range(c + 1, 4):
                if matrix[4*r + c] != 0:
                    matrix = row_swap(matrix, c, r)
                    i = row_swap(i, c, r)

        # Make 0's in column for rows that aren't pivot row
        for r in range(4):
            if r != c: # not the pivot row
                r_piv = matrix[4*r + c]
                if r_piv != 0:
                    piv = matrix[4*c + c]
                    scalar = r_piv / piv
                    matrix = row_mul(matrix, c, scalar)
                    matrix = row_sub(matrix, c, r)
                    i = row_mul(i, c, scalar)
                    i = row_sub(i, c, r)

        # Put matrix in reduced row-echelon form.
        piv = matrix[4*c + c]
        matrix = row_mul(matrix, c, 1/piv)
        i = row_mul(i, c, 1/piv)
    return i


def row_swap(matrix, r1, r2):
    lo = min(r1, r2)
    hi = max(r1, r2)
    values = (matrix[:lo*4]
            + matrix[hi*4:hi*4 + 4]
            + matrix[lo*4 + 4:hi*4]
            + matrix[lo*4:lo*4 + 4]
            + matrix[hi*4 + 4:])
    return Mat4(values)


def row_mul(matrix, r, x):
    values = (matrix[:r*4]
            + tuple(v * x for v in matrix[r*4:r*4 + 4])
            + matrix[r*4 + 4:])
    return Mat4(values)


# subtracts r1 from r2
def row_sub(matrix, r1, r2):
    row1 = matrix[4*r1:4*r1 + 4]
    row2 = matrix[4*r2:4*r2 + 4]
    values = (matrix[:r2*4]
            + tuple(v2 - v1 for (v1, v2) in zip(row1, row2))
            + matrix[r2*4 + 4:])
    return Mat4(values)


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
        return self[index*4:index*4+4]

    def column(self, index):
        return self[index::4]

    def __add__(self, other):
        assert len(other) == 16, "Can only multiply with other Mat4 types"
        return Mat4(tuple(s + o for s, o in zip(self, other)))

    def __sub__(self, other):
        assert len(other) == 16, "Can only multiply with other Mat4 types"
        return Mat4(tuple(s - o for s, o in zip(self, other)))

    def __pos__(self):
        return self

    def __neg__(self):
        return Mat4(tuple(-v for v in self))

    def __invert__(self):
        return inverse(self)

    def __round__(self, n=None):
        return Mat4(tuple(round(v, n) for v in self))

    def __mul__(self, other):
        assert len(other) == 16, "Can only multiply with other Mat4 types"
        return Mat4(tuple(s * o for s, o in zip(self, other)))

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
