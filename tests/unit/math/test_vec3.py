import math
import pytest
from pyglet.math import Vec3


def test_create():
    assert Vec3(1, 2, 3) == Vec3(1, 2, 3)
    assert Vec3(0) == Vec3(0, 0, 0)
    # assert Vec3(1) == Vec3(1, 1, 1)  # not supported
    with pytest.raises(TypeError):
        Vec3(1, 2, 3, 4)


def test_access():
    """Test Vec3 class."""
    # Basic access
    v = Vec3(1, 2, 3)
    assert v.x == 1
    assert v.y == 2
    assert v.z == 3
    assert v[0] == 1
    assert v[1] == 2
    assert v[2] == 3
    assert v == (1, 2, 3)


def test_comparison():
    assert Vec3(1, 2, 3) == Vec3(1, 2, 3)
    assert Vec3(1, 2, 3) != Vec3(2, 1, 3)
    assert Vec3(1, 2, 3) == (1, 2, 3)
    assert (1, 2, 3) == Vec3(1, 2, 3)


def test_swizzle():
    """Test swizzle."""
    v = Vec3(1, 2, 3)
    assert v.xyz == (1, 2, 3)
    assert v.yxz == (2, 1, 3)
    assert v.yzx == (2, 3, 1)
    assert v.zyx == (3, 2, 1)
    assert v.xy == (1, 2)
    assert v.xxxx == (1, 1, 1, 1)
    assert v.xyzx == (1, 2, 3, 1)

    with pytest.raises(AttributeError):
        v.xxxxx


def test_mutability():
    v = Vec3(1, 2, 3)
    with pytest.raises(AttributeError):
        v.x = 1
    with pytest.raises(AttributeError):
        v.y = 1
    with pytest.raises(AttributeError):
        v.z = 1
    with pytest.raises(TypeError):
        v[0] = 1  # __setitem__ is not supported

    # Swizzle is an output-only operation
    with pytest.raises(AttributeError):
        v.xyz = (1, 2, 3)
    with pytest.raises(AttributeError):
        v.yxz = (2, 1, 3)
    with pytest.raises(AttributeError):
        v.yzx = (2, 3, 1)
    with pytest.raises(AttributeError):
        v.zyx = (3, 2, 1)
    with pytest.raises(AttributeError):
        v.xy = (1, 2)
    with pytest.raises(AttributeError):
        v.xxxx = (1, 1, 1, 1)
    with pytest.raises(AttributeError):
        v.xyzx = (1, 2, 3, 1)


def test_len():
    """Len of the collection is always 2."""
    assert len(Vec3(0)) == 3


def test_max_min():
    assert max(Vec3(1, 2, 3)) == 3
    assert max(Vec3(1, -2, 0)) == 1

    assert min(Vec3(1, 2, 3)) == 1
    assert min(Vec3(1, -2, 0)) == -2


def test_add():
    assert Vec3(1, 2, 3) + Vec3(4, 5, 6) == Vec3(5, 7, 9)

    assert Vec3(1, 2, 3) + 3 == Vec3(4, 5, 6)
    assert 2 + Vec3(1, 2, 3) == Vec3(3, 4, 5)

    assert Vec3(1, 2, 3) + (4, 5, 6) == Vec3(5, 7, 9)
    assert (1, 2, 3) + Vec3(4, 5, 6) == Vec3(5, 7, 9)

    v = Vec3(1, 2, 3)
    v += 1
    assert v == Vec3(2, 3, 4)

    v = Vec3(1, 2, 3)
    v += Vec3(1, 2, 3)
    assert v == Vec3(2, 4, 6)

    v = Vec3(1, 2, 3)
    v += (1, 2, 3)
    assert v == Vec3(2, 4, 6)


def test_radd():
    # The goals should be distinct and unreachable by
    # simple mis-addition of the values below
    goal_x = -6709.0
    goal_y = 359.0
    goal_z = 7829.0
    seq = [
        Vec3(3.0, 0.0, 0.0),
        (0.0, 5.0, 0.0),
        Vec3(0.0, 0.0, 7.0),

        Vec3(goal_x, goal_y, goal_z),

        # Opposites of the block above
        (-3.0, 0.0, 0.0),
        Vec3(0.0, -5.0, 0.0),
        (0.0, 0.0, -7.0)
    ]
    assert sum(seq) == Vec3(goal_x, goal_y, goal_z)


def test_sub():
    assert Vec3(1, 2, 3) - Vec3(3, 4, 6) == Vec3(-2, -2, -3)

    assert Vec3(1, 2, 3) - 3 == Vec3(-2, -1, 0)
    assert 2 - Vec3(1, 2, 3) == Vec3(1, 0, -1)

    assert Vec3(1, 2, 3) - (4, 5, 6) == Vec3(-3, -3, -3)
    assert (1, 2, 3) - Vec3(3, 4, 5) == Vec3(-2, -2, -2)

    v = Vec3(1, 2, 3)
    v -= Vec3(1, 1, 1)
    assert v == Vec3(0, 1, 2)

    v = Vec3(1, 2, 3)
    v -= (1, 2, 3)
    assert v == Vec3(0, 0, 0)

    v = Vec3(0, 1, 2)
    v -= 1
    assert v == Vec3(-1, 0, 1)


def test_mul():
    assert Vec3(2, 3, 4) * Vec3(4, 6, 7) == Vec3(8, 18, 28)

    assert Vec3(1, 2, 3) * 2 == Vec3(2, 4, 6)
    assert 2 * Vec3(1, 2, 3) == Vec3(2, 4, 6)

    assert Vec3(1, 2, 3) * (2, 2, 2) == Vec3(2, 4, 6)
    assert (1, 2, 3) * Vec3(2, 2, 2) == Vec3(2, 4, 6)

    v = Vec3(1, 2, 3)
    v *= Vec3(2, 2, 2)
    assert v == Vec3(2, 4, 6)

    v = Vec3(1, 2, 3)
    v *= 2
    assert v == Vec3(2, 4, 6)

    v = Vec3(1, 2, 3)
    v *= Vec3(2, 2, 2)
    assert v == Vec3(2, 4, 6)


def test_truediv():
    assert Vec3(2, 4, 6) / Vec3(2, 2, 2) == Vec3(1, 2, 3)

    assert Vec3(2, 4, 6) / 2.0 == Vec3(1, 2, 3)
    assert 1.0 / Vec3(0.5, 0.5, 0.5) == Vec3(2, 2, 2)

    assert (2, 4, 6) / Vec3(2, 2, 2) == Vec3(1, 2, 3)
    assert Vec3(2, 4, 6) / (2, 2, 2) == Vec3(1, 2, 3)

    v = Vec3(2, 4, 6)
    v /= Vec3(2, 2, 2)
    assert v == Vec3(1, 2, 3)

    v = Vec3(2, 4, 6)
    v /= 2
    assert v == Vec3(1, 2, 3)

    v = Vec3(2, 4, 6)
    v /= (2, 2, 2)
    assert v == Vec3(1, 2, 3)

    with pytest.raises(ZeroDivisionError):
        Vec3(1, 2, 3) / 0
    with pytest.raises(ZeroDivisionError):
        Vec3(1, 2, 3) / (0, 0, 0)
    with pytest.raises(ZeroDivisionError):
        Vec3(1, 2, 3) / Vec3(0, 0, 0)
    with pytest.raises(ZeroDivisionError):
        v = Vec3(1, 2, 3)
        v /= 0


def test_floordiv():
    assert Vec3(2.1, 4.1, 6.1) // Vec3(2, 2, 2) == Vec3(1, 2, 3)

    assert Vec3(2.1, 4.1, 6.1) // 2 == Vec3(1, 2, 3)
    assert 4.1 // Vec3(2, 4, 1) == Vec3(2, 1, 4)

    assert (1, 2, 3) // Vec3(0.5, 0.5, 0.5) == Vec3(2, 4, 6)
    assert Vec3(1, 2, 3) // (0.5, 0.5, 0.5) == Vec3(2, 4, 6)

    v = Vec3(4, 8, 12)
    v //= 2
    assert v == Vec3(2, 4, 6)

    v = Vec3(4, 8, 12)
    v //= Vec3(2, 2, 2)
    assert v == Vec3(2, 4, 6)

    v = Vec3(4, 8, 12)
    v //= (2, 2, 2)
    assert v == Vec3(2, 4, 6)

    with pytest.raises(ZeroDivisionError):
        Vec3(1, 2, 3) // 0
    with pytest.raises(ZeroDivisionError):
        Vec3(1, 2, 3) // (0, 0, 0)
    with pytest.raises(ZeroDivisionError):
        Vec3(1, 2, 3) // Vec3(0, 0, 0)
    with pytest.raises(ZeroDivisionError):
        v = Vec3(1, 2, 3)
        v //= 0


def test_length():
    assert Vec3(1, 0, 0).length() == 1
    assert Vec3(0, 1, 0).length() == 1
    assert Vec3(0, 0, 1).length() == 1

    assert Vec3(3, 0, 0).length() == 3
    assert Vec3(0, 3, 0).length() == 3
    assert Vec3(0, 0, 3).length() == 3

    assert Vec3(1, 1, 0).length() == pytest.approx(1.41421, abs=1e-5)
    assert Vec3(-1, -1, 0).length() == pytest.approx(1.41421, abs=1e-5)
    assert Vec3(1, 1, 1).length() == pytest.approx(1.73205, abs=1e-5)


def test_length_squared():
    assert Vec3(1, 0, 0).length_squared() == 1
    assert Vec3(0, -1, 0).length_squared() == 1
    assert Vec3(0, 0, 1).length_squared() == 1

    assert Vec3(3, 0, 0).length_squared() == 9
    assert Vec3(0, 3, 0).length_squared() == 9
    assert Vec3(0, 0, 3).length_squared() == 9

    assert Vec3(1, 1, 0).length_squared() == 2
    assert Vec3(-1, -1, 0).length_squared() == 2
    assert Vec3(-1, -1, 1).length_squared() == 3


def test_abs():
    assert abs(Vec3(1, 2, 3)) == Vec3(1, 2, 3)
    assert abs(Vec3(-1, -2, -3)) == Vec3(1, 2, 3)


def test_neg():
    """Negate the vector."""
    assert -Vec3(1, 2, 3) == Vec3(-1, -2, -3)


def test_round():
    """Round the vector values"""
    assert round(Vec3(1.1, 2.2, 3.3)) == Vec3(1, 2, 3)
    assert round(Vec3(1.1, 2.2, 3.3), 1) == Vec3(1.1, 2.2, 3.3)


def test_ceil():
    assert math.ceil(Vec3(1.1, 2.2, 3.3)) == Vec3(2, 3, 4)


def test_floor():
    assert math.floor(Vec3(1.1, 2.2, 3.3)) == Vec3(1, 2, 3)


def test_trunc():
    assert math.trunc(Vec3(1.1, 2.2, 3.3)) == Vec3(1, 2, 3) 


def test_mod():
    assert Vec3(3, 4, 5) % Vec3(2, 2, 2) == Vec3(1, 0, 1)
    assert Vec3(3, 4, 5) % 2 == Vec3(1, 0, 1)

    assert Vec3(3.2, 4.2, 5.2) % 2 == pytest.approx(Vec3(1.2, 0.2, 1.2), abs=1e-5)


def test_pow():
    assert Vec3(2, 3, 4) ** Vec3(2, 2, 2) == Vec3(4, 9, 16)
    assert Vec3(2, 3, 4) ** 2 == Vec3(4, 9, 16)


def test_lt():
    """Compares the length of the vectors."""
    assert Vec3(1, 2, 3) < Vec3(2, 3, 4)

    assert Vec3(1, 2, 3) < (2, 3, 4)
    assert (1, 2, 3) < Vec3(2, 3, 4)


def test_sum():
    assert sum(Vec3(1, 2, 3)) == 6


def test_cross():
    assert Vec3(1, 0, 0).cross(Vec3(0, 1, 0)) == Vec3(0, 0, 1)
    assert Vec3(0, 1, 0).cross(Vec3(0, 0, 1)) == Vec3(1, 0, 0)
    assert Vec3(0, 0, 1).cross(Vec3(1, 0, 0)) == Vec3(0, 1, 0)


def test_dot():
    assert Vec3(1, 0, 0).dot(Vec3(1, 0, 0)) == 1
    assert Vec3(0, 1, 0).dot(Vec3(0, 1, 0)) == 1
    assert Vec3(0, 0, 1).dot(Vec3(0, 0, 1)) == 1

    assert Vec3(0, 1, 0).dot(Vec3(1, 0, 0)) == 0
    assert Vec3(1, 0, 0).dot(Vec3(0, 1, 0)) == 0
    assert Vec3(1, 0, 0).dot(Vec3(0, 0, 1)) == 0


def test_lerp():
    assert Vec3(1, 2, 3).lerp(Vec3(2, 3, 4), 0) == Vec3(1, 2, 3)
    assert Vec3(1, 2, 3).lerp(Vec3(2, 3, 4), 1) == Vec3(2, 3, 4)
    assert Vec3(1, 2, 3).lerp(Vec3(2, 3, 4), 0.5) == Vec3(1.5, 2.5, 3.5)


def test_distance():
    assert Vec3(0, 0, 0).distance(Vec3(1, 0, 0)) == 1
    assert Vec3(0, 0, 0).distance(Vec3(0, 1, 0)) == 1
    assert Vec3(0, 0, 0).distance(Vec3(0, 0, 1)) == 1

    assert Vec3(1, 2, 3).distance(Vec3(2, 3, 4)) == pytest.approx(1.73205, abs=1e-5)


def test_normalize():
    assert Vec3(1, 0, 0).normalize() == Vec3(1, 0, 0)
    assert Vec3(0, 1, 0).normalize() == Vec3(0, 1, 0)
    assert Vec3(0, 0, 1).normalize() == Vec3(0, 0, 1)

    assert Vec3(1, 1, 1).normalize() == Vec3(1 / math.sqrt(3), 1 / math.sqrt(3), 1 / math.sqrt(3))
    assert Vec3(-1, -1, -1).normalize() == -Vec3(1 / math.sqrt(3), 1 / math.sqrt(3), 1 / math.sqrt(3))


def test_clamp():
    assert Vec3(-10, 0, 10).clamp(-20, 0) == Vec3(-10, 0, 0)
    assert Vec3(-10, 0, 10).clamp(-5, 5) == Vec3(-5, 0, 5)
    assert Vec3(-10, 0, 10).clamp(0, 20) == Vec3(0, 0, 10)
    assert Vec3(-10, 0, 10).clamp(-20, 20) == Vec3(-10, 0, 10)

    assert Vec3(-10, 0, 10).clamp(Vec3(-20, -5, 0), Vec3(0, 5, 10)) == Vec3(-10, 0, 10)
    assert Vec3(-10, 0, 10).clamp(Vec3(-20, 5, 0), Vec3(0, 20, 10)) == Vec3(-10, 5, 10) 
    assert Vec3(-10, 0, 10).clamp(Vec3(0, -5, 0), Vec3(20, 5, 10)) == Vec3(0, 0, 10)

    # Revert if necessary for perf
    assert Vec3(-1, 50, 50).clamp(Vec3(0, 0, 0), 10) == Vec3(0, 10, 10)
    assert Vec3(-1, -1, 50).clamp(0, Vec3(10, 10, 10)) == Vec3(0, 0, 10)


def test_index():
    with pytest.raises(NotImplementedError):
        Vec3(0).index(0)


def test_bool():
    v = Vec3()
    assert not v

    v = Vec3(0.1, 2.0, 33.3)
    assert v

    v = Vec3(1.0, -1.0, 0.0)
    assert v