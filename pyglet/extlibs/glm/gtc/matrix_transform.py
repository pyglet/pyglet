# -*- coding: utf-8 -*-

# The MIT License (MIT)
#
# Copyright (c) 2014-2017 Shi Chi(Mack Stone)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import math

from ..detail.func_geometric import *
from ..detail.type_mat4x4 import Mat4x4


def translate(m, v):
    """Builds a translation 4 * 4 matrix created from a vector of 3 components.
    :param :class: Mat4x4 m: Input matrix multiplied by this translation matrix.
    :param :class: Vec4 v: Coordinates of a translation vector.
    :return: matrix4x4
    :rtype: Mat4x4
    .. code-block:: python

        import glm
        m = glm.tranlate(glm:mat4(1.0), glm.vec3(1.0))
        # m[0][0] == 1.0, m[0][1] == 0.0, m[0][2] == 0.0, m[0][3] == 0.0
        # m[1][0] == 0.0, m[1][1] == 1.0, m[1][2] == 0.0, m[1][3] == 0.0
        # m[2][0] == 0.0, m[2][1] == 0.0, m[2][2] == 1.0, m[2][3] == 0.0
        # m[3][0] == 1.0, m[3][1] == 1.0, m[3][2] == 1.0, m[3][3] == 1.0

    .. seealso::

        gtc_matrix_transform
        gtx_transform
        :func: translate(x, y, z)
        :func: translate(m, x, y, z)
        :func: translate(v)"""
    result = Mat4x4(m)
    result[3] = m[0] * v[0] + m[1] * v[1] + m[2] * v[2] + m[3]
    return result

def rotate(m, angle, axis):
    """Builds a rotation 4 * 4 matrix created from an axis vector and an angle.
    :param :class: Mat4x4 m: Input matrix multiplied by this rotation matrix.
    :param float v: Rotation angle expressed in radians or degrees.
    :param :class: Vec3 axis: Rotation axis, recommanded to be normalized.
    :return: matrix4x4
    :rtype: Mat4x4

    .. seealso::
        gtc_matrix_transform
        gtx_transform
        :func: rotate(angle, x, y, z)
        :func: rotate(m, angle, x, y, z)
        :func: rotate(angle, v)"""
    a = math.radians(angle)

    c = math.cos(a)
    s = math.sin(a)

    axis = Vec3(normalize(axis))
    temp = (1. - c) * axis

    rmat = Mat4x4()
    rmat[0][0] = c + temp[0] * axis[0]
    rmat[0][1] = 0 + temp[0] * axis[1] + s * axis[2]
    rmat[0][2] = 0 + temp[0] * axis[2] - s * axis[1]

    rmat[1][0] = 0 + temp[1] * axis[0] - s * axis[2]
    rmat[1][1] = c + temp[1] * axis[1]
    rmat[1][2] = 0 + temp[1] * axis[2] + s * axis[0]

    rmat[2][0] = 0 + temp[2] * axis[0] + s * axis[1]
    rmat[2][1] = 0 + temp[2] * axis[1] - s * axis[0]
    rmat[2][2] = c + temp[2] * axis[2]

    result = Mat4x4()
    result[0] = m[0] * rmat[0][0] + m[1] * rmat[0][1] + m[2] * rmat[0][2]
    result[1] = m[0] * rmat[1][0] + m[1] * rmat[1][1] + m[2] * rmat[1][2]
    result[2] = m[0] * rmat[2][0] + m[1] * rmat[2][1] + m[2] * rmat[2][2]
    result[3] = m[3]
    return result

def perspective(fovy, aspect, zNear, zFar):
    """Creates a matrix for a symetric perspective-view frustum.
    :param float fovy: radian or degrees
    :param float aspect: aspect ratio
    :param float zNear: near plane
    :param float zFar: far plane
    :return: matrix4x4
    :rtype: Mat4x4"""

    assert(aspect != 0)
    assert(zFar != zNear)

    rad = math.radians(fovy)
    tanHalfFovy = math.tan((rad / 2))

    result = Mat4x4(0.0)
    result[0][0] = 1. / (aspect * tanHalfFovy)
    result[1][1] = 1. / tanHalfFovy
    result[2][2] = -(zFar + zNear) / (zFar - zNear)
    result[2][3] = -1.
    result[3][2] = -(2. * zFar * zNear) / (zFar - zNear)
    return result

def lookAt(eye, center, up):
    """Creates a viewing matrix. The matrix maps the reference point to 
    the negative z axis and the eye point to the origin. When a typical 
    projection matrix is used, the center of the scene therefore maps to 
    the center of the viewport. Similarly, the direction described by the 
    UP vector projected onto the viewing plane is mapped to the positive y 
    axis so that it points upward in the viewport. The UP vector must not be 
    parallel to the line of sight from the eye point to the reference point.
    :param Vec3 eye: Specifies the position of the eye point 
    :param Vec3 center: Reference point indicating the center of the scene 
    :param Vec3 up: Up direction
    :rtype: Mat4x4"""

    def cross( a, b):
        return Vec3(a.y*b.z-a.z*b.y, -(a.x*b.z-a.z*b.x), a.x*b.y-a.y*b.x)

    f = normalize(center - eye)
    s = normalize(cross(f, up))
    u = cross(s, f)

    Result = Mat4x4(1.0)
    Result[0][0] = s.x
    Result[1][0] = s.y
    Result[2][0] = s.z
    Result[0][1] = u.x
    Result[1][1] = u.y
    Result[2][1] = u.z
    Result[0][2] =-f.x
    Result[1][2] =-f.y
    Result[2][2] =-f.z
    Result[3][0] =-dot(s, eye)
    Result[3][1] =-dot(u, eye)
    Result[3][2] = dot(f, eye)
    return Result

