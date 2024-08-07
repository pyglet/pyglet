import math
import pytest
from pyglet.math import Vec4


def test_create():
    assert Vec4(1, 2, 3, 4) == Vec4(1, 2, 3, 4)
    assert Vec4(0) == Vec4(0, 0, 0, 0)
    # assert Vec4(1) == Vec4(1, 1, 1, 1)  # not supported
    with pytest.raises(TypeError):
        Vec4(1, 2, 3, 4, 5)


def test_access():
    """Test Vec4 class."""
    # Basic access
    v = Vec4(1, 2, 3, 4)
    assert v.x == 1
    assert v.y == 2
    assert v.z == 3
    assert v.w == 4
    assert v[0] == 1
    assert v[1] == 2
    assert v[2] == 3
    assert v[3] == 4
    assert v == (1, 2, 3, 4)


def test_comparison():
    assert Vec4(1, 2, 3, 4) == Vec4(1, 2, 3, 4)
    assert Vec4(1, 2, 3, 4) != Vec4(2, 1, 3, 4)
    assert Vec4(1, 2, 3, 4) == (1, 2, 3, 4)
    assert (1, 2, 3, 4) == Vec4(1, 2, 3, 4)


def test_swizzle():
    """Test swizzle."""
    v = Vec4(1, 2, 3, 4)
    assert v.xyzw == (1, 2, 3, 4)
    assert v.yxzw == (2, 1, 3, 4)
    assert v.yzxw == (2, 3, 1, 4)
    assert v.zyxw == (3, 2, 1, 4)
    assert v.xy == (1, 2)
    assert v.xyz == (1, 2, 3)
    assert v.wzyx == (4, 3, 2, 1)
    assert v.xxxx == (1, 1, 1, 1)

    with pytest.raises(AttributeError):
        v.xxxxx


def test_mutability():
    v = Vec4(1, 2, 3, 4)
    with pytest.raises(AttributeError):
        v.x = 1
    with pytest.raises(AttributeError):
        v.y = 1
    with pytest.raises(AttributeError):
        v.z = 1
    with pytest.raises(AttributeError):
        v.w = 1
    with pytest.raises(TypeError):
        v[0] = 1  # __setitem__ is not supported

    # Swizzle is an output-only operation
    with pytest.raises(AttributeError):
        v.xyzw = (1, 2, 3, 4)
    with pytest.raises(AttributeError):
        v.yxzw = (2, 1, 3, 4)
    with pytest.raises(AttributeError):
        v.yzxw = (2, 3, 1, 4)
    with pytest.raises(AttributeError):
        v.zyxw = (3, 2, 1, 4)
    with pytest.raises(AttributeError):
        v.xy = (1, 2)
    with pytest.raises(AttributeError):
        v.xyz = (1, 2, 3)
    with pytest.raises(AttributeError):
        v.wzyx = (4, 3, 2, 1)
    with pytest.raises(AttributeError):
        v.xxxx = (1, 1, 1, 1)


def test_len():
    """Len of the collection is always 2."""
    assert len(Vec4(0)) == 4


def test_max_min():
    assert max(Vec4(1, 2, 3, 0)) == 3
    assert max(Vec4(1, -2, 0, 1)) == 1

    assert min(Vec4(1, 2, 3, 4)) == 1
    assert min(Vec4(1, -2, 0, 4)) == -2


def test_add():
    assert Vec4(1, 2, 3, 4) + Vec4(4, 5, 6, 7) == Vec4(5, 7, 9, 11)

    assert Vec4(1, 2, 3, 4) + 3 == Vec4(4, 5, 6, 7)
    assert 2 + Vec4(1, 2, 3, 4) == Vec4(3, 4, 5, 6)

    assert Vec4(1, 2, 3, 4) + (4, 5, 6, 7) == Vec4(5, 7, 9, 11)
    assert (1, 2, 3, 4) + Vec4(4, 5, 6, 7) == Vec4(5, 7, 9, 11)

    v = Vec4(1, 2, 3, 4)
    v += 1
    assert v == Vec4(2, 3, 4, 5)

    v = Vec4(1, 2, 3, 4)
    v += Vec4(1, 2, 3, 4)
    assert v == Vec4(2, 4, 6, 8)

    v = Vec4(1, 2, 3, 4)
    v += (1, 2, 3, 4)
    assert v == Vec4(2, 4, 6, 8)


def test_radd():
    # The goals should be distinct and unreachable by
    # simple mis-addition of the values below
    goal_x = -3251.0
    goal_y = 593.0
    goal_z = 3847.0
    goal_w = 7621.0
    seq = [
        Vec4(3.0, 0.0, 0.0, 0.0),
        (0.0, 5.0, 0.0, 0.0),
        Vec4(0.0, 0.0, 7.0, 0.0),
        (0.0, 0.0, 0.0, 9.0),

        Vec4(goal_x, goal_y, goal_z, goal_w),

        # Opposites of the block above
        (0.0, 0.0, 0.0, -9.0),
        Vec4(-3.0, 0.0, 0.0, 0.0),
        (0.0, -5.0, 0.0, 0.0),
        Vec4(0.0, 0.0, -7.0, 0.0)
    ]
    assert sum(seq) == Vec4(goal_x, goal_y, goal_z, goal_w)




def test_sub():
    assert Vec4(1, 2, 3, 4) - Vec4(5, 6, 7, 8) == Vec4(-4, -4, -4, -4)

    assert Vec4(1, 2, 3, 4) - 3 == Vec4(-2, -1, 0, 1)
    assert 2 - Vec4(1, 2, 3, 4) == Vec4(1, 0, -1, -2)

    assert Vec4(1, 2, 3, 4) - (5, 6, 7, 8) == Vec4(-4, -4, -4, -4)
    assert (1, 2, 3, 4) - Vec4(5, 6, 7, 8) == Vec4(-4, -4, -4, -4)

    v = Vec4(1, 2, 3, 4)
    v -= Vec4(1, 1, 1, 1)
    assert v == Vec4(0, 1, 2, 3)

    v = Vec4(1, 2, 3, 4)
    v -= (1, 2, 3, 4)
    assert v == Vec4(0, 0, 0, 0)

    v = Vec4(0, 1, 2, 3)
    v -= 1
    assert v == Vec4(-1, 0, 1, 2)


def test_mul():
    assert Vec4(2, 3, 4, 5) * Vec4(4, 6, 8, 10) == Vec4(8, 18, 32, 50)

    assert Vec4(1, 2, 3, 4) * 2 == Vec4(2, 4, 6, 8)
    assert 2 * Vec4(1, 2, 3, 4) == Vec4(2, 4, 6, 8)

    assert Vec4(1, 2, 3, 4) * (2, 2, 2, 2) == Vec4(2, 4, 6, 8)
    assert (1, 2, 3, 4) * Vec4(2, 2, 2, 2) == Vec4(2, 4, 6, 8)

    v = Vec4(1, 2, 3, 4)
    v *= Vec4(2, 2, 2, 2)
    assert v == Vec4(2, 4, 6, 8)

    v = Vec4(1, 2, 3, 4)
    v *= 2
    assert v == Vec4(2, 4, 6, 8)

    v = Vec4(1, 2, 3, 4)
    v *= Vec4(2, 2, 2, 2)
    assert v == Vec4(2, 4, 6, 8)


def test_truediv():
    assert Vec4(2, 4, 6, 8) / Vec4(2, 2, 2, 2) == Vec4(1, 2, 3, 4)

    assert Vec4(2, 4, 6, 8) / 2.0 == Vec4(1, 2, 3, 4)
    assert 1.0 / Vec4(0.5, 0.5, 0.5, 0.5) == Vec4(2, 2, 2, 2)

    assert (2, 4, 6, 8) / Vec4(2, 2, 2, 2) == Vec4(1, 2, 3, 4)
    assert Vec4(2, 4, 6, 8) / (2, 2, 2, 2) == Vec4(1, 2, 3, 4)

    v = Vec4(2, 4, 6, 8)
    v /= Vec4(2, 2, 2, 2)
    assert v == Vec4(1, 2, 3, 4)

    v = Vec4(2, 4, 6, 8)
    v /= 2
    assert v == Vec4(1, 2, 3, 4)

    v = Vec4(2, 4, 6, 8)
    v /= (2, 2, 2, 2)
    assert v == Vec4(1, 2, 3, 4)

    with pytest.raises(ZeroDivisionError):
        Vec4(1, 2, 3, 4) / 0
    with pytest.raises(ZeroDivisionError):
        Vec4(1, 2, 3, 4) / (0, 0, 0, 0)
    with pytest.raises(ZeroDivisionError):
        Vec4(1, 2, 3, 4) / Vec4(0, 0, 0, 0)
    with pytest.raises(ZeroDivisionError):
        v = Vec4(1, 2, 3, 4)
        v /= 0


def test_floordiv():
    assert Vec4(2.1, 4.1, 6.1, 8.1) // Vec4(2, 2, 2, 2) == Vec4(1, 2, 3, 4)

    assert Vec4(2.1, 4.1, 6.1, 8.1) // 2 == Vec4(1, 2, 3, 4)
    assert 8.1 // Vec4(2, 4, 8, 1) == Vec4(4, 2, 1, 8)

    assert (1, 2, 3, 4) // Vec4(0.5, 0.5, 0.5, 0.5) == Vec4(2, 4, 6, 8)
    assert Vec4(1.1, 2.1, 3.1, 4.1) // (0.5, 0.5, 0.5, 0.5) == Vec4(2, 4, 6, 8)

    v = Vec4(4, 8, 12, 16)
    v //= 2
    assert v == Vec4(2, 4, 6, 8)

    v = Vec4(4, 8, 12, 16)
    v //= Vec4(2, 2, 2, 2)
    assert v == Vec4(2, 4, 6, 8)

    v = Vec4(4, 8, 12, 16)
    v //= (2, 2, 2, 2)
    assert v == Vec4(2, 4, 6, 8)

    with pytest.raises(ZeroDivisionError):
        Vec4(1, 2, 3, 4) // 0
    with pytest.raises(ZeroDivisionError):
        Vec4(1, 2, 3, 4) // (0, 0, 0, 0)
    with pytest.raises(ZeroDivisionError):
        Vec4(1, 2, 3, 4) // Vec4(0, 0, 0, 0)
    with pytest.raises(ZeroDivisionError):
        v = Vec4(1, 2, 3, 4)
        v //= 0


def test_length():
    assert Vec4(1, 0, 0, 0).length() == 1
    assert Vec4(0, 1, 0, 0).length() == 1
    assert Vec4(0, 0, 1, 0).length() == 1
    assert Vec4(0, 0, 0, 1).length() == 1

    assert Vec4(3, 0, 0, 0).length() == 3
    assert Vec4(0, 3, 0, 0).length() == 3
    assert Vec4(0, 0, 3, 0).length() == 3
    assert Vec4(0, 0, 0, 3).length() == 3

    assert Vec4(1, 1, 0, 0).length() == pytest.approx(1.41421, abs=1e-5)
    assert Vec4(-1, -1, 0, 0).length() == pytest.approx(1.41421, abs=1e-5)
    assert Vec4(1, 1, 1, 0).length() == pytest.approx(1.73205, abs=1e-5)
    assert Vec4(1, 1, 1, 1).length() == pytest.approx(2, abs=1e-5)


def test_length_squared():
    assert Vec4(1, 0, 0, 0).length_squared() == 1
    assert Vec4(0, -1, 0, 0).length_squared() == 1
    assert Vec4(0, 0, 1, 0).length_squared() == 1
    assert Vec4(0, 0, 0, 1).length_squared() == 1

    assert Vec4(3, 0, 0, 0).length_squared() == 9
    assert Vec4(0, 3, 0, 0).length_squared() == 9
    assert Vec4(0, 0, 3, 0).length_squared() == 9
    assert Vec4(0, 0, 0, 3).length_squared() == 9

    assert Vec4(1, 1, 0, 0).length_squared() == 2
    assert Vec4(-1, -1, 0, 0).length_squared() == 2
    assert Vec4(-1, -1, 1, 0).length_squared() == 3
    assert Vec4(-1, -1, 1, 1).length_squared() == 4


def test_abs():
    assert abs(Vec4(1, 2, 3, 4)) == Vec4(1, 2, 3, 4)
    assert abs(Vec4(-1, -2, -3, -4)) == Vec4(1, 2, 3, 4)


def test_neg():
    """Negate the vector."""
    assert -Vec4(1, 2, 3) == Vec4(-1, -2, -3)


def test_round():
    """Round the vector values"""
    assert round(Vec4(1.1, 2.2, 3.3, 4.4)) == Vec4(1, 2, 3, 4)
    assert round(Vec4(1.11, 2.22, 3.33, 4.44), 1) == Vec4(1.1, 2.2, 3.3, 4.4)


def test_ceil():
    assert math.ceil(Vec4(1.1, 2.2, 3.3, 4.4)) == Vec4(2, 3, 4, 5)


def test_floor():
    assert math.floor(Vec4(1.1, 2.2, 3.3, 4.4)) == Vec4(1, 2, 3, 4)


def test_trunc():
    assert math.trunc(Vec4(1.1, 2.2, 3.3, 4.4)) == Vec4(1, 2, 3, 4)


def test_mod():
    assert Vec4(3, 4, 5, 6) % Vec4(2, 2, 2, 2) == Vec4(1, 0, 1, 0)
    assert Vec4(3, 4, 5, 6) % 2 == Vec4(1, 0, 1, 0)

    assert Vec4(3.2, 4.2, 5.2, 6.2) % 2 == pytest.approx(Vec4(1.2, 0.2, 1.2, 0.2), abs=1e-5)


def test_pow():
    assert Vec4(2, 3, 4, 5) ** Vec4(2, 2, 2, 2) == Vec4(4, 9, 16, 25)
    assert Vec4(2, 3, 4, 5) ** 2 == Vec4(4, 9, 16, 25)


def test_lt():
    """Compares the length of the vectors."""
    assert Vec4(1, 2, 3, 0) < Vec4(2, 3, 4, 0)
    assert Vec4(2, 3, 4, 0) > Vec4(1, 2, 3, 0)

    assert Vec4(1, 2, 3, 4) < (2, 3, 4, 5)
    assert (1, 2, 3, 4) < Vec4(2, 3, 4, 5)


def test_sum():
    assert sum(Vec4(1, 2, 3, 4)) == 10


def test_lerp():
    assert Vec4(1, 2, 3, 4).lerp(Vec4(2, 3, 4, 5), 0) == Vec4(1, 2, 3, 4)
    assert Vec4(1, 2, 3, 4).lerp(Vec4(2, 3, 4, 5), 0.5) == Vec4(1.5, 2.5, 3.5, 4.5)
    assert Vec4(1, 2, 3, 4).lerp(Vec4(2, 3, 4, 5), 1) == Vec4(2, 3, 4, 5)


def test_distance():
    assert Vec4(0, 0, 0, 0).distance(Vec4(1, 0, 0, 0)) == 1
    assert Vec4(0, 0, 0, 0).distance(Vec4(0, 1, 0, 0)) == 1
    assert Vec4(0, 0, 0, 0).distance(Vec4(0, 0, 1, 0)) == 1
    assert Vec4(0, 0, 0, 0).distance(Vec4(0, 0, 0, 1)) == 1

    assert Vec4(0, 0, 0, 0).distance(Vec4(3, 0, 0, 0)) == 3
    assert Vec4(0, 0, 0, 0).distance(Vec4(0, 3, 0, 0)) == 3
    assert Vec4(0, 0, 0, 0).distance(Vec4(0, 0, 3, 0)) == 3
    assert Vec4(0, 0, 0, 0).distance(Vec4(0, 0, 0, 3)) == 3

    assert Vec4(1, 2, 3, 4).distance(Vec4(2, 3, 4, 5)) == pytest.approx(2.0, abs=1e-5)


def test_normalize():
    assert Vec4(1, 0, 0).normalize() == Vec4(1, 0, 0)
    assert Vec4(0, 1, 0).normalize() == Vec4(0, 1, 0)
    assert Vec4(0, 0, 1).normalize() == Vec4(0, 0, 1)

    assert Vec4(1, 1, 1).normalize() == Vec4(1 / math.sqrt(3), 1 / math.sqrt(3), 1 / math.sqrt(3))
    assert Vec4(-1, -1, -1).normalize() == -Vec4(1 / math.sqrt(3), 1 / math.sqrt(3), 1 / math.sqrt(3))

    v = Vec4(1, 2, 3, 4)
    l = v.length()
    assert Vec4(1, 2, 3, 4).normalize() == Vec4(1 / l, 2 / l, 3 / l, 4 / l)


def test_clamp():
    assert Vec4(-6, -2, 2, 6).clamp(-8, 0) == Vec4(-6, -2, 0, 0)
    assert Vec4(-6, -2, 2, 6).clamp(-4, 4) == Vec4(-4, -2, 2, 4)
    assert Vec4(-6, -2, 2, 6).clamp(0, 8) == Vec4(0, 0, 2, 6)

    assert Vec4(-10, 0, 10, 20).clamp(Vec4(-20, -4, 0, 0), Vec4(0, 4, 8, 10)) == Vec4(-10, 0, 8, 10)
    # Revert if necessary for perf
    assert Vec4(-1, -1, 50, 50).clamp(Vec4(0, 0, 0, 0), 10) == Vec4(0, 0, 10, 10)
    assert Vec4(-1, -1, 50, 50).clamp(0, Vec4(10, 10, 10, 10)) == Vec4(0, 0, 10, 10)


def test_dot():
    assert Vec4(1, 0, 0, 0).dot(Vec4(1, 0, 0, 0)) == 1

    assert Vec4(1, 0, 0, 0).dot(Vec4(0, 1, 0, 0)) == 0
    assert Vec4(0, 1, 0, 0).dot(Vec4(1, 0, 0, 0)) == 0
    assert Vec4(0, 0, 1, 0).dot(Vec4(1, 0, 0, 0)) == 0
    assert Vec4(0, 0, 0, 1).dot(Vec4(1, 0, 0, 0)) == 0

    assert Vec4(1, 0, 0, 1).dot(Vec4(1, 0, 0, 1)) == 2
    

def test_index():
    with pytest.raises(NotImplementedError):
        Vec4(0).index(None)


def test_bool():
    v = Vec4()
    assert not v

    v = Vec4(0.1, 2.0, 33.3, 0.04)
    assert v

    v = Vec4(-1.0, 1.0, 0.0, 0.0)
    assert v
