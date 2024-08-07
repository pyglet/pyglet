"""
Using PyGLM/glm to verify commonly supported operators and functions.
"""
import math

import pytest
from pyglet.math import Vec2

# mix
# min / max
# angle (between two vectors)
# from_heading (from angle to vector)


def test_create():
    assert Vec2
    assert Vec2(1, 2) == Vec2(1, 2)
    # assert Vec2(1) == Vec2(1, 1)  # not supported
    with pytest.raises(TypeError):
        Vec2(1, 2, 3)


def test_access():
    """Test Vec2 class."""
    # Basic access
    v = Vec2(1, 2)
    assert v.x == 1
    assert v.y == 2
    assert v[0] == 1
    assert v[1] == 2
    assert v == (1, 2)


def test_comparison():
    assert Vec2(1, 2) == Vec2(1, 2)
    assert Vec2(1, 2) != Vec2(2, 1)
    assert Vec2(1, 2) == (1, 2)
    assert (1, 2) == Vec2(1, 2)


def test_swizzle():
    """Test swizzle."""
    v = Vec2(1, 2)
    assert v.xy == (1, 2)
    assert v.yx == (2, 1)
    assert v.xx == (1, 1)
    assert v.yy == (2, 2)
    assert v.xyxy == (1, 2, 1, 2)

    with pytest.raises(AttributeError):
        v.xxxxx


def test_mutability():
    v = Vec2(1, 2)
    with pytest.raises(AttributeError):
        v.x = 1
    with pytest.raises(AttributeError):
        v.y = 1
    with pytest.raises(TypeError):
        v[0] = 1  # __setitem__ is not supported

    # Swizzle is an output-only operation
    with pytest.raises(AttributeError):
        v.xy = (1, 2)
    with pytest.raises(AttributeError):
        v.yx = (2, 1)
    with pytest.raises(AttributeError):
        v.xx = (1, 1)
    with pytest.raises(AttributeError):
        v.yy = (2, 2)
    with pytest.raises(AttributeError):
        v.xyxy = (1, 2, 1, 2)


def test_len():
    """Len of the collection is always 2."""
    assert len(Vec2(0)) == 2


def test_max_min():
    assert max(Vec2(1, 2)) == 2
    assert max(Vec2(1, -2)) == 1

    assert min(Vec2(1, 2)) == 1
    assert min(Vec2(1, -2)) == -2


def test_add():
    assert Vec2(1, 2) + Vec2(3, 4) == Vec2(4, 6)

    assert Vec2(1, 2) + 3 == Vec2(4, 5)
    assert 2 + Vec2(1, 2) == Vec2(3, 4)

    assert Vec2(1, 2) + (3, 4) == Vec2(4, 6)
    assert (1, 2) + Vec2(3, 4) == Vec2(4, 6)

    v = Vec2(1, 2)
    v += 1
    assert v == Vec2(2, 3)

    v = Vec2(1, 3)
    v += Vec2(3, 4)
    assert v == Vec2(4, 7)

    v = Vec2(1, 2)
    v += (3, 4)
    assert v == Vec2(4, 6)


def test_radd():
    # These should be distinct and  unreachable through
    # simple mis-addition of the mirrored values below.
    goal_x = -1901.0
    goal_y = 7919.0
    pairs = [
        # A few (+even, -odd) Vec2s + tuples
        Vec2( -8.0,     7.0),
        ( -6.0,     5.0),
        Vec2( -4.0,     3.0),
        ( -2.0,     1.0),

        Vec2(goal_x, goal_y),

        # Negatives of the block above the marker line
        (  2.0, -    1.0),
        Vec2(  4.0, -    3.0),
        (  6.0, -    5.0),
        Vec2(  8.0, -    7.0),
    ]
    assert sum(pairs) == Vec2(goal_x, goal_y)


def test_sub():
    assert Vec2(1, 2) - Vec2(3, 4) == Vec2(-2, -2)

    assert Vec2(1, 2) - 3 == Vec2(-2, -1)
    assert 2 - Vec2(1, 2) == Vec2(1, 0)

    assert Vec2(1, 2) - (3, 4) == Vec2(-2, -2)
    assert (1, 2) - Vec2(3, 4) == Vec2(-2, -2)

    v = Vec2(1, 2)
    v -= Vec2(1, 1)
    assert v == Vec2(0, 1)

    v = Vec2(1, 2)
    v -= (1, 2)
    assert v == Vec2(0, 0)

    v = Vec2(0, 1)
    v -= 1
    assert v == Vec2(-1, 0)


def test_mul():
    assert Vec2(2, 3) * Vec2(4, 5) == Vec2(8, 15)

    assert Vec2(1, 2) * 2 == Vec2(2, 4)
    assert 2 * Vec2(1, 2) == Vec2(2, 4)

    assert Vec2(1, 2) * (2, 2) == Vec2(2, 4)
    assert (1, 2) * Vec2(2, 2) == Vec2(2, 4)

    v = Vec2(1, 2)
    v *= Vec2(2, 2)
    assert v == Vec2(2, 4)

    v = Vec2(1, 2)
    v *= 2
    assert v == Vec2(2, 4)

    v = Vec2(1, 2)
    v *= Vec2(2, 2)
    assert v == Vec2(2, 4)


def test_truediv():
    assert Vec2(2, 4) / Vec2(2, 2) == Vec2(1, 2)

    assert Vec2(2, 4) / 2.0 == Vec2(1, 2)
    assert 1.0 / Vec2(0.5, 0.5) == Vec2(2, 2)

    assert (2, 4) / Vec2(2, 2) == Vec2(1, 2)
    assert Vec2(2, 4) / (2, 2) == Vec2(1, 2)

    v = Vec2(2, 4)
    v /= Vec2(2, 2)
    assert v == Vec2(1, 2)

    v = Vec2(2, 4)
    v /= 2
    assert v == Vec2(1, 2)

    v = Vec2(2, 4)
    v /= (2, 2)
    assert v == Vec2(1, 2)

    with pytest.raises(ZeroDivisionError):
        Vec2(1, 2) / Vec2(0, 0)
    with pytest.raises(ZeroDivisionError):
        Vec2(1, 2) / (0, 0)
    with pytest.raises(ZeroDivisionError):
        (1, 2) / Vec2(0, 0)
    with pytest.raises(ZeroDivisionError):
        Vec2(1, 2) / 0
    with pytest.raises(ZeroDivisionError):
        v = Vec2(1, 2)
        v /= 0


def test_floordiv():
    assert Vec2(2.5, 4.5) // Vec2(2, 2) == Vec2(1, 2)

    assert Vec2(2.5, 4.5) // 2 == Vec2(1, 2)
    assert 4.2 // Vec2(2, 4) == Vec2(2, 1)

    assert (1, 2) // Vec2(0.5, 0.5) == Vec2(2, 4)
    assert Vec2(1, 2) // (0.5, 0.5) == Vec2(2, 4)

    v = Vec2(4, 8)
    v //= 2
    assert v == Vec2(2, 4)

    v = Vec2(4, 8)
    v //= Vec2(2, 2)
    assert v == Vec2(2, 4)

    v = Vec2(4, 8)
    v //= (2, 2)
    assert v == Vec2(2, 4)

    with pytest.raises(ZeroDivisionError):
        Vec2(1, 2) // Vec2(0, 0)
    with pytest.raises(ZeroDivisionError):
        Vec2(1, 2) // (0, 0)
    with pytest.raises(ZeroDivisionError):
        (1, 2) // Vec2(0, 0)
    with pytest.raises(ZeroDivisionError):
        Vec2(1, 2) // 0
    with pytest.raises(ZeroDivisionError):
        v = Vec2(1, 2)
        v //= 0


def test_length():
    assert Vec2(1, 0).length() == 1
    assert Vec2(0, 1).length() == 1

    assert Vec2(3, 0).length() == 3
    assert Vec2(0, 3).length() == 3

    assert Vec2(1, 1).length() == pytest.approx(1.41421, abs=1e-5)
    assert Vec2(-1, -1).length() == pytest.approx(1.41421, abs=1e-5)


def test_length_squared():
    assert Vec2(1, 0).length_squared() == 1
    assert Vec2(0, -1).length_squared() == 1

    assert Vec2(3, 0).length_squared() == 9
    assert Vec2(0, 3).length_squared() == 9

    assert Vec2(1, 1).length_squared() == 2
    assert Vec2(-1, -1).length_squared() == 2


def test_abs():
    assert abs(Vec2(1, 2)) == Vec2(1, 2)
    assert abs(Vec2(-1, -2)) == Vec2(1, 2)


def test_neg():
    """Negate the vector."""
    assert -Vec2(1, 2) == Vec2(-1, -2)


def test_round():
    """Round the vector values"""
    assert round(Vec2(1.1, 2.2)) == Vec2(1, 2)
    assert round(Vec2(1.1, 2.2), 1) == Vec2(1.1, 2.2)


def test_ceil():
    assert math.ceil(Vec2(1.1, 2.2)) == Vec2(2, 3)


def test_floor():
    assert math.floor(Vec2(1.1, 2.2)) == Vec2(1, 2)


def test_trunc():
    assert math.trunc(Vec2(1.1, 2.2)) == Vec2(1, 2)


def test_mod():
    assert Vec2(3, 4) % Vec2(2, 2) == Vec2(1, 0)
    assert Vec2(3, 4) % 2 == Vec2(1, 0)

    assert Vec2(5.3, 4.7) % 2 == pytest.approx(Vec2(1.3, 0.7), abs=1e-5)


def test_pow():
    assert Vec2(2, 3) ** Vec2(2, 3) == Vec2(4, 27)
    assert Vec2(2, 3) ** 2 == Vec2(4, 9)


def test_lt():
    """Compares the length of the vectors."""
    assert Vec2(1, 2) < Vec2(2, 3)

    assert Vec2(1, 2) < (2, 3)
    assert (1, 2) < Vec2(2, 3)


def test_sum():
    assert sum(Vec2(1, 2)) == 3


def test_from_polar():
    """Create a vector from polar coordinates."""
    assert Vec2.from_polar(math.radians(90)) == pytest.approx(Vec2(0, 1), abs=1e-5)
    assert Vec2.from_polar(math.radians(180)) == pytest.approx(Vec2(-1, 0), abs=1e-5)
    assert Vec2.from_polar(math.radians(270)) == pytest.approx(Vec2(0, -1), abs=1e-5)


def test_from_heading():
    """Create a vector from a heading."""
    assert Vec2.from_heading(0, length=1) == Vec2(1, 0)
    assert Vec2.from_heading(math.radians(90), length=2) == pytest.approx(Vec2(0, 2), abs=1e-5)
    assert Vec2.from_heading(math.radians(180), length=3) == pytest.approx(Vec2(-3, 0), abs=1e-5)
    assert Vec2.from_heading(math.radians(-90), length=4) == pytest.approx(Vec2(0, -4), abs=1e-5)


def test_heading():
    assert Vec2(1, 0).heading() == 0
    assert Vec2(0, 1).heading() == math.radians(90)
    assert Vec2(-1, 0).heading() == math.radians(180)
    assert Vec2(0, -1).heading() == math.radians(-90)


def test_lerp():
    """Linear interpolation between two vectors."""
    assert Vec2(1, 2).lerp(Vec2(3, 4), 0.5) == Vec2(2, 3)
    assert Vec2(1, 2).lerp(Vec2(3, 4), 0) == Vec2(1, 2)
    assert Vec2(1, 2).lerp(Vec2(3, 4), 1) == Vec2(3, 4)
    assert Vec2(1, 2).lerp((3, 4), 0.5) == Vec2(2, 3)


def test_step():
    """Step function."""
    assert Vec2(1, 1).step(Vec2(1, 1)) == Vec2(1, 1)
    assert Vec2(0, 2).step(Vec2(1, 1)) == Vec2(0, 1)
    assert Vec2(2, 0).step(Vec2(1, 1)) == Vec2(1, 0)
    assert Vec2(3, 3).step(Vec2(1, 1)) == Vec2(1, 1)


def test_reflect():
    """Reflect vector off another vector."""
    assert Vec2(1, 0). reflect(Vec2(1, 0)) == Vec2(-1, 0)
    assert Vec2(1, 0). reflect(Vec2(0, 1)) == Vec2(1, 0)
    assert Vec2(1, 0). reflect(Vec2(1, 0)) == Vec2(-1, 0)


def test_rotate():
    """Rotate vector by degrees."""
    assert Vec2(1, 0).rotate(math.radians(90)) == pytest.approx(Vec2(0, 1), abs=1e-5)
    assert Vec2(1, 0).rotate(math.radians(180)) == pytest.approx(Vec2(-1, 0), abs=1e-5)
    assert Vec2(1, 0).rotate(math.radians(270)) == pytest.approx(Vec2(0, -1), abs=1e-5)
    assert Vec2(1, 0).rotate(math.radians(360)) == pytest.approx(Vec2(1, 0), abs=1e-5)


def test_distance():
    """Calculate the distance between two vectors."""
    assert Vec2(1, 2).distance(Vec2(3, 4)) == pytest.approx(2.82843, abs=1e-5)
    assert Vec2(-1, -2).distance(Vec2(3, 4)) == pytest.approx(7.21110, abs=1e-5)


def test_normalize():
    """Normalize various vectors."""
    assert Vec2(1, 2).normalize() == pytest.approx(Vec2(0.447214, 0.894427), abs=1e-5)
    assert Vec2(2, 1).normalize() == pytest.approx(Vec2(0.894427, 0.447214), abs=1e-5)
    assert Vec2(-1, -2).normalize() == pytest.approx(Vec2(-0.447214, -0.894427), abs=1e-5)
    assert Vec2(-2, -1).normalize() == pytest.approx(Vec2(-0.894427, -0.447214), abs=1e-5)
    assert Vec2(0, 0).normalize() == Vec2(0, 0)


def test_clamp():
    """Attempt to clamp vector using all possible combinations."""
    assert Vec2(-10, 10).clamp(-10, 10) == Vec2(-10, 10)
    assert Vec2(-10, 10).clamp(-20, 5) == Vec2(-10, 5)
    assert Vec2(-10, 10).clamp(-5, 5) == Vec2(-5, 5)
    assert Vec2(-10, 10).clamp(5, 15) == Vec2(5, 10)
    assert Vec2(-10, 10).clamp(5, 5) == Vec2(5, 5)

    assert Vec2(-10, 10).clamp(Vec2(-20, -20), Vec2(20, 20)) == Vec2(-10, 10)
    assert Vec2(-10, 10).clamp(Vec2(-5, 5), Vec2(5, 5)) == Vec2(-5, 5)

    # Revert if necessary for perf
    assert Vec2(-1, 50).clamp(Vec2(0, 0), 10) == Vec2(0, 10)
    assert Vec2(-1,  50).clamp(0, Vec2(10, 10)) == Vec2(0, 10)


def test_dot():
    assert Vec2(1, 0).dot(Vec2(1, 0)) == 1  # same direction
    assert Vec2(1, 0).dot(Vec2(0, 1)) == 0  # perpendicular
    assert Vec2(1, 2).dot(Vec2(3, 4)) == 11

    assert Vec2(-1, 0).dot((-1, 0)) == 1  # same direction
    assert Vec2(-1, 0).dot((0, -1)) == 0  # perpendicular
    assert Vec2(-1, -2).dot((-3, -4)) == 11


def test_index():
    with pytest.raises(NotImplementedError):
        Vec2(0).index(0)


def test_bool():
    v = Vec2()
    assert not v

    v = Vec2(0.1, 2.0)
    assert v

    v = Vec2(-1.0, 1.0)
    assert v
