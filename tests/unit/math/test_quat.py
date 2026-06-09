import pytest

import math

from pyglet.math import Quaternion, Mat3, Mat4


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
