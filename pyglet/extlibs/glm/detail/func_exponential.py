# -*- coding: utf-8 -*-

# The MIT License (MIT)
#
# Copyright (c) 2014-2018 Shi Chi(Mack Stone)
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

from .type_vec3 import Vec3
from .type_vec4 import Vec4



def inversesqrt(x):
    """Returns the reciprocal of the positive square root of x.

    :param x: inversesqrt function is defined for input values of x defined in the range [0, inf+) in the limit of the type precision.
    :type x: Floating-point scalar or vector

    .. seealso::
        `GLSL inversesqrt man page <http://www.opengl.org/sdk/docs/manglsl/xhtml/inversesqrt.xml>`_
        `GLSL 4.20.8 specification, section 8.2 Exponential Functions <http://www.opengl.org/registry/doc/GLSLangSpec.4.20.8.pdf>`_"""
    if isinstance(x, float):
        return 1.0 / math.sqrt(x)
    #elif isinstance(x, Vec2):
        #tx = inversesqrt(x.x)
        #ty = inversesqrt(x.y)
        #return Vec2(tx, ty)
    elif isinstance(x, Vec3):
        tx = inversesqrt(x.x)
        ty = inversesqrt(x.y)
        tz = inversesqrt(x.z)
        return Vec3(tx, ty, tz)
    elif isinstance(x, Vec4):
        tx = inversesqrt(x.x)
        ty = inversesqrt(x.y)
        tz = inversesqrt(x.z)
        tw = inversesqrt(x.w)
        return Vec3(tx, ty, tz, tw)

