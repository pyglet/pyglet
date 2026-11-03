import pytest

import math

from pyglet.math import Quaternion, Mat3, Mat4, Vec4


@pytest.fixture
def identity():
    return Quaternion(1, 0, 0, 0)


def isclose(q1: Quaternion, q2: Quaternion, tolerance: float = 0.000001) -> bool:
    return (math.isclose(q1.w, q2.w, rel_tol=tolerance, abs_tol=tolerance) and
            math.isclose(q1.x, q2.x, rel_tol=tolerance, abs_tol=tolerance) and
            math.isclose(q1.y, q2.y, rel_tol=tolerance, abs_tol=tolerance) and
            math.isclose(q1.z, q2.z, rel_tol=tolerance, abs_tol=tolerance))


def test_to_mat3():
    # TODO: Needs improvement. Just checking identity matrix.
    q = Quaternion()
    assert q.to_mat3() == Mat3()


def test_to_mat4():
    # TODO: Needs improvement. Just checking identity matrix.
    q = Quaternion()
    assert q.to_mat4() == Mat4()


def test_norm_preservation():
    # normalizing before or after multiplication should match.
    p = Quaternion(1, 2, 3, 4)
    q = Quaternion(5, 6, 7, 8)
    assert isclose((p @ q).normalize(), p.normalize() @ q.normalize())


def test_conjugate_rule():
    p = Quaternion(1, 2, 3, 4)
    q = Quaternion(5, 6, 7, 8)
    assert (p @ q).conjugate() == q.conjugate() @ p.conjugate()


def test_inverse_property(identity):
    q = Quaternion(1, 2, 3, 4)
    assert isclose(q @ ~q, identity)
    assert isclose(~q @ q, identity)


def test_rotation_composition(identity):
    # 36 degrees rotation around the X axis
    r = Quaternion(math.cos(math.pi / 10), math.sin(math.pi / 10), 0, 0)

    # Compose 10 rotations (360 degrees total)
    result = r
    for _ in range(9):
        result = result @ r

    negative_identity = Quaternion(-1, 0, 0, 0)

    # Check if result is close to either identity or negative identity
    assert isclose(result, identity) or isclose(result, negative_identity)


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
