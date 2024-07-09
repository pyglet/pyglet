import pytest
from pyglet.math import Quaternion, Mat3, Mat4


def test_create():
    q = Quaternion()
    assert q.x == 0
    assert q.y == 0
    assert q.z == 0
    assert q.w == 1
    assert q.length() == 1


def test_from_mat3():
    with pytest.raises(NotImplementedError):
        Quaternion.from_mat3()


def test_from_mat4():
    with pytest.raises(NotImplementedError):
        Quaternion.from_mat4()


def test_to_mat3():
    # TODO: Needs improvement. Just checking identity matrix.
    q = Quaternion()
    assert q.to_mat3() == Mat3()


def test_to_mat4():
    # TODO: Needs improvement. Just checking identity matrix.
    q = Quaternion()
    assert q.to_mat4() == Mat4()
