import math as _math
import operator as _operator


def create_orthogonal(left, right, bottom, top, znear, zfar):
    """Create a Mat4 with orthographic projection."""
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
    """Create a Mat4 with perspective projection."""
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
    """Scale a Matrix."""
    temp = list(matrix)
    temp[0] *= x
    temp[5] *= y
    temp[10] *= z
    return Mat4(temp)


def translate(matrix, x=0, y=0, z=0):
    """Translate a Matrix along x, y, and z axis."""
    return Mat4(matrix) @ Mat4((1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1))


def rotate(matrix, angle=0, x=0, y=0, z=0):
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

    return matrix @ Mat4((ra, rb, rc, 0, re, rf, rg, 0, ri, rj, rk, 0, 0, 0, 0, 1))


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

        A Matrix can be created with list or tuple of 16 values.
        If nothing is provided, an "identity Matrix" will be created
        (1.0 on the main diagonal). Matrix objects are immutable, so
        all operations return a new Mat4 object.

        :Parameters:
            `values` : tuple of float or int
                A tuple containing 16 values.
        """
        assert values is None or len(values) == 16, "A 4x4 Matrix requires 16 values"
        values = values or (1.0, 0.0, 0.0, 0.0,
                            0.0, 1.0, 0.0, 0.0,
                            0.0, 0.0, 1.0, 0.0,
                            0.0, 0.0, 0.0, 1.0)
        return super().__new__(Mat4, values)

    def __add__(self, other):
        assert len(other) == 16, "Can only multiply with other Mat4 types"
        return Mat4(tuple(s + o for s, o in zip(self, other)))

    def __sub__(self, other):
        assert len(other) == 16, "Can only multiply with other Mat4 types"
        return Mat4(tuple(s - o for s, o in zip(self, other)))

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
