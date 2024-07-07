"""
Using PyGLM/glm to verify commonly supported operators and functions.
"""
import math

import pytest
from pyglet.math import Vec2


def test_access():
    """Test Vec2 class."""
    # Basic access
    v = Vec2(1, 2)
    assert v.x == 1
    assert v.y == 2
    assert v[0] == 1
    assert v[1] == 2
    assert v == (1, 2)


def test_swizzle():
    """Test swizzle."""
    v = Vec2(1, 2)
    assert v.xy == (1, 2)


def test_mutability():
    v = Vec2(1, 2)
    with pytest.raises(AttributeError):
        v.x = 1
    with pytest.raises(AttributeError):
        v.y = 1
    with pytest.raises(TypeError):
        v[0] = 1  # __setitem__ is not supported


def test_add():
    assert Vec2(1, 2) + Vec2(3, 4) == Vec2(4, 6)
    assert Vec2(1, 2) + 3 == Vec2(4, 5)
    assert Vec2(1, 2) + (3, 4) == Vec2(4, 6)
    assert 2 + Vec2(1, 2) == Vec2(3, 4)
    v = Vec2(1, 2)
    v += 1
    assert v == Vec2(2, 3)
    v += Vec2(1, 2)
    assert v == Vec2(3, 5)


def test_sub():
    assert Vec2(1, 2) - Vec2(3, 4) == Vec2(-2, -2)
    assert Vec2(1, 2) - 3
    assert Vec2(1, 2) - (3, 4) == Vec2(-2, -2)
    assert 2 - Vec2(1, 2) == Vec2(-1, 0)
    v = Vec2(1, 2)
    v -= 1
    assert v == Vec2(0, 1)
    v -= Vec2(1, 2)
    assert v == Vec2(-1, -1)


def test_mul():
    assert Vec2(2, 3) * Vec2(4, 5) == Vec2(8, 15)
    assert Vec2(1, 2) * 2 == Vec2(2, 4)
    assert 2 * Vec2(1, 2) == Vec2(2, 4)


def test_truediv():
    assert Vec2(2, 4) / 2.0 == Vec2(1, 2)
    # assert 1 / Vec2(0.5, 0.5) == Vec2(2, 2)  # Allowed by division order is wrong
    assert Vec2(2, 4) / Vec2(2, 2) == Vec2(1, 2)  # Not supported
    v = Vec2(2, 4)
    v /= 2
    assert v == Vec2(1, 2)
    v /= Vec2(2, 2)
    assert v == Vec2(0.5, 1)


def test_floordiv():
    assert Vec2(2, 4) // 2 == Vec2(1, 2)
    # assert 1 / Vec2(0.5, 0.5) == Vec2(2, 2)  # Allowed by division order is wrong
    assert Vec2(2, 4) // Vec2(2, 2) == Vec2(1, 2)  # Not supported
    v = Vec2(4, 8)
    v //= 2
    assert v == Vec2(2, 4)
    v //= Vec2(2, 2)
    assert v == Vec2(1, 2)


def test_abs():
    # NOTE: Possibly this should just be normal abs
    assert abs(Vec2(1, 2)) == pytest.approx(2.23606, abs=1e-5)


def test_neg():
    """Negate the vector."""
    assert -Vec2(1, 2) == Vec2(-1, -2)


def test_round():
    """Round the vector values"""
    assert round(Vec2(1.1, 2.2)) == Vec2(1, 2)
    assert round(Vec2(1.1, 2.2), 1) == Vec2(1.1, 2.2)


def test_lt():
    """Compares the length of the vectors."""
    assert Vec2(1, 2) < Vec2(2, 3)
    with pytest.raises(TypeError):
        assert Vec2(1, 2) < (2, 3)
    assert not Vec2(1, 2) < Vec2(1, 2)


def test_sum():
    # assert sum(Vec2(1, 2), Vec2(3, 4)) == Vec2(4, 6)  # ??
    pass


def test_from_polar():
    """Create a vector from polar coordinates."""
    assert Vec2.from_polar(mag=1, angle=math.radians(90)) == pytest.approx(Vec2(0, 1), abs=1e-5)
    assert Vec2.from_polar(mag=1, angle=math.radians(180)) == pytest.approx(Vec2(-1, 0), abs=1e-5)
    assert Vec2.from_polar(mag=1, angle=math.radians(270)) == pytest.approx(Vec2(0, -1), abs=1e-5)


def test_from_magnitude():
    """Recreate the vector with a new magnitude keeping the heading"""
    assert Vec2(2, 0).from_magnitude(0) == Vec2(0, 0)
    assert Vec2(2, 0).from_magnitude(1) == Vec2(1, 0)
    assert Vec2(2, 0).from_magnitude(2) == Vec2(2, 0)

    assert Vec2(0, 2).from_magnitude(0) == Vec2(0, 0)
    assert Vec2(0, 2).from_magnitude(2) == Vec2(0, 2)
    assert Vec2(0, 2).from_magnitude(4) == Vec2(0, 4)


def test_from_heading():
    """Recreate the vector with a new heading keeping the length"""
    vec = Vec2(2, 0)
    assert vec.from_heading(0) == Vec2(2, 0)
    assert vec.from_heading(math.radians(90)) == pytest.approx(Vec2(0, 2), abs=1e-5)
    assert vec.from_heading(math.radians(180)) == pytest.approx(Vec2(-2, 0), abs=1e-5)
    assert vec.from_heading(math.radians(270)) == pytest.approx(Vec2(0, -2), abs=1e-3)


def test_heading():
    pass


def test_mag():
    """Calculate the magnitude of the vector."""
    assert Vec2(1, 0).mag == 1
    assert Vec2(1, 1).mag == pytest.approx(1.41421, abs=1e-5)
    assert Vec2(1, 2).mag == pytest.approx(2.23607, abs=1e-5)


def test_limit():
    """Limit the magnitude of the vector."""
    assert Vec2(1, 0).limit(1) == Vec2(1, 0)
    assert Vec2(1, 0).limit(0.5) == Vec2(0.5, 0)
    assert Vec2(1, 0).limit(0) == Vec2(0, 0)


def test_lerp():
    """Linear interpolation between two vectors."""
    assert Vec2(1, 2).lerp(Vec2(3, 4), 0.5) == Vec2(2, 3)
    assert Vec2(1, 2).lerp(Vec2(3, 4), 0) == Vec2(1, 2)
    assert Vec2(1, 2).lerp(Vec2(3, 4), 1) == Vec2(3, 4)


def test_reflect():
    """Reflect vector off another vector."""
    assert Vec2(1, 0). reflect(Vec2(1, 0)) == Vec2(-1, 0)
    assert Vec2(1, 0). reflect(Vec2(0, 1)) == Vec2(1, 0)
    assert Vec2(1, 0). reflect(Vec2(1, 0)) == Vec2(-1, 0)


def rest_rotate():
    """Rotate vector by degrees."""
    assert Vec2(1, 0).rotate(90) == Vec2(0, 1)
    assert Vec2(1, 0).rotate(180) == Vec2(-1, 0)
    assert Vec2(1, 0).rotate(270) == Vec2(0, -1)
    assert Vec2(1, 0).rotate(360) == Vec2(1, 0)


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


def test_dot():
    assert Vec2(1, 0).dot(Vec2(1, 0)) == 1  # same direction
    assert Vec2(1, 0).dot(Vec2(0, 1)) == 0  # perpendicular
    assert Vec2(1, 2).dot(Vec2(3, 4)) == 11

    assert Vec2(-1, 0).dot(Vec2(-1, 0)) == 1  # same direction
    assert Vec2(-1, 0).dot(Vec2(0, -1)) == 0  # perpendicular
    assert Vec2(-1, -2).dot(Vec2(-3, -4)) == 11
