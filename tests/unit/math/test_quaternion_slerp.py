"""Unit rotation interpolation needs stable endpoints and no zero-dot division."""

import math

import pytest

from pyglet.math import Quaternion, Vec4


def rotation(angle, axis=2):
    values = [math.cos(angle / 2), 0.0, 0.0, 0.0]
    values[axis + 1] = math.sin(angle / 2)
    return Quaternion(*values)


@pytest.mark.parametrize("axis", [0, 1, 2])
@pytest.mark.parametrize("t", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_orthogonal_quaternions(axis, t):
    # Use an exact zero dot, not cos(pi/2)'s small floating-point residual.
    target = [0.0, 0.0, 0.0, 0.0]
    target[axis + 1] = 1.0
    result = Quaternion().slerp(Quaternion(*target), t)
    assert result == pytest.approx(rotation(math.pi * t, axis), abs=1e-12)
    assert result.length() == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("t", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_identical_rotations_remain_unit(sign, t):
    start = Quaternion(0.5, 0.5, 0.5, 0.5)
    result = start.slerp(start * sign, t)
    assert result == pytest.approx(start, abs=1e-12)
    assert result.length() == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize("t", [0.25, 0.5, 0.75])
@pytest.mark.parametrize("sign", [1, -1])
def test_nearly_identical_rotations(t, sign):
    result = Quaternion().slerp(rotation(0.002) * sign, t)
    assert result == pytest.approx(rotation(0.002 * t), rel=0, abs=1e-10)
    assert result.length() == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize("t", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_shortest_path_across_negative_dot(t):
    start = rotation(math.radians(170))
    target = rotation(math.radians(-170))
    result = start.slerp(target, t)
    assert result == pytest.approx(rotation(math.radians(170 + 20 * t)), abs=1e-12)
    assert result.length() == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize("t", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_ordinary_quarter_turn(t):
    result = Quaternion().slerp(rotation(math.pi / 2, 1), t)
    assert result == pytest.approx(rotation(math.pi / 2 * t, 1), abs=1e-12)
    assert result.length() == pytest.approx(1.0, abs=1e-12)


def test_roundoff_above_one_is_clamped():
    start = Quaternion(math.nextafter(1.0, math.inf), 0, 0, 0)
    result = start.slerp(start, 0.5)
    assert result == pytest.approx(Quaternion(), abs=1e-12)


def test_interpolated_rotation_does_not_scale_vertices():
    start = Quaternion(0.5, 0.5, 0.5, 0.5)
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        matrix = start.slerp(start, t).to_mat4()
        vertex = matrix @ Vec4(1, 0, 0, 0)
        assert sum(value * value for value in vertex[:3]) == pytest.approx(1.0, abs=1e-12)
