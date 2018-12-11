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

import numbers

from . import type_vec


class Vec4(type_vec.BaseVec4):
    """vec4 class number type: float"""

    def __new__(cls, *args, **kwargs):
        inList = []
        if kwargs:
            inList.append(kwargs.get('x', 0))
            inList.append(kwargs.get('y', 0))
            inList.append(kwargs.get('z', 0))
            inList.append(kwargs.get('w', 0))
        elif args:
            argsLen = len(args)
            if argsLen == 1:
                arg0 = args[0]
                if isinstance(arg0, type_vec.BaseVec4):
                    inList = arg0.tolist()
                elif isinstance(arg0, type_vec.BaseVec3):
                    inList = arg0.tolist() + [0]
                elif isinstance(arg0, type_vec.BaseVec2):
                    inList = arg0.tolist() + [0, 0]
                elif isinstance(arg0, type_vec.BaseVec1):
                    inList = arg0.tolist() + [0, 0, 0]
                elif isinstance(arg0, list) or isinstance(arg0, tuple):
                    il = []
                    arg0Len = len(arg0)
                    if arg0Len == 1:
                        il = list(arg0) + [0, 0, 0]
                    elif arg0Len == 2:
                        il = list(arg0) + [0, 0]
                    elif arg0Len == 3:
                        il = list(arg0) + [0]
                    elif arg0Len == 4:
                        il = list(arg0)
                    inList = il
                elif isinstance(arg0, numbers.Number):
                    inList = [arg0, arg0, arg0, arg0]
            elif argsLen == 2:
                arg0, arg1 = args
                if isinstance(arg0, type_vec.BaseVec3):
                    inList = arg0.tolist() + [arg1]
                elif isinstance(arg1, type_vec.BaseVec3):
                    inList = [arg0] + arg1.tolist()
                elif isinstance(arg0, type_vec.BaseVec2) and isinstance(arg1, type_vec.BaseVec2):
                    inList = arg0.tolist() + arg1.tolist()
                elif isinstance(arg0, numbers.Number) and isinstance(arg1, numbers.Number):
                    inList = args + [0, 0]
            elif argsLen == 3:
                arg0, arg1, arg2 = args
                if isinstance(arg0, numbers.Number) and isinstance(arg1, numbers.Number) and isinstance(arg2, numbers.Number):
                    inList = list(args) + [0]
                elif isinstance(arg0, type_vec.BaseVec2) and isinstance(arg1, numbers.Number) and isinstance(arg2, numbers.Number):
                    inList = arg0.tolist() + [arg1, arg2]
                elif isinstance(arg0, numbers.Number) and isinstance(arg1, type_vec.BaseVec2) and isinstance(arg2, numbers.Number):
                    inList = [arg0] + arg1.tolist() + [arg2]
                elif isinstance(arg0, numbers.Number) and isinstance(arg1, numbers.Number) and isinstance(arg2, type_vec.BaseVec2):
                    inList = [arg0, arg1] + arg2.tolist()
            elif argsLen == 4:
                inList = args
            else:
                inList = args[:4]
        if not args and not kwargs:
            inList = [0, 0, 0, 0]

        return type_vec.BaseVec4.__new__(cls, Vec4.dataType, inList)

    def __add__(self, value):
        if isinstance(value, Vec4):
            return Vec4(self.x + value.x, self.y + value.y,
                        self.z + value.z, self.w + value.w)
        else:
            return Vec4(self.x + value, self.y + value,
                        self.z + value, self.w + value)

    def __radd__(self, value):
        return Vec4(value + self.x, value + self.y,
                    value + self.z, value + self.w)

    def __sub__(self, value):
        if isinstance(value, Vec4):
            return Vec4(self.x - value.x, self.y - value.y,
                        self.z - value.z, self.w - value.w)
        else:
            return Vec4(self.x - value, self.y - value,
                        self.z - value, self.w - value)

    def __rsub__(self, value):
        return Vec4(value - self.x, value - self.y,
                    value - self.z, value - self.w)

    def __mul__(self, value):
        if isinstance(value, Vec4):
            return Vec4(self.x * value.x, self.y * value.y,
                        self.z * value.z, self.w * value.w)
        else:
            return Vec4(self.x * value, self.y * value,
                        self.z * value, self.w * value)

    def __rmul__(self, value):
        return Vec4(value * self.x, value * self.y,
                    value * self.z, value * self.w)

    def __div__(self, value):
        if isinstance(value, Vec4):
            return Vec4(self.x / value.x, self.y / value.y,
                        self.z / value.z, self.w / value.w)
        else:
            return Vec4(self.x / value, self.y / value,
                        self.z / value, self.w / value)

    def __rdiv__(self, value):
        return Vec4(value / self.x, value / self.y,
                    value / self.z, value / self.w)

    def __truediv__(self, value):
        if isinstance(value, Vec4):
            return Vec4(self.x / float(value.x), self.y / float(value.y),
                        self.z / float(value.z), self.w / float(value.w))
        else:
            return Vec4(self.x / float(value), self.y / float(value),
                        self.z / float(value), self.w / float(value))

    def __rtruediv__(self, value):
        v = float(value)
        return Vec4(v / self.x, v / self.y, v / self.z, v / self.w)

    def __neg__(self):
        return Vec4(-self.x, -self.y, -self.z, -self.w)

    def __mod__(self, value):
        if isinstance(value, Vec4):
            return Vec4(self.x % value.x, self.y % value.y,
                        self.z % value.z, self.w % value.w)
        else:
            return Vec4(self.x % value, self.y % value,
                        self.z % value, self.w % value)

    def __rmod__(self, value):
        return Vec4(value % self.x, value % self.y, value % self.z, value.w % self.w)

    def __and__(self, value):
        if isinstance(value, Vec4):
            return Vec4(self.x & value.x, self.y & value.y,
                        self.z & value.z, self.w & value.w)
        else:
            return Vec4(self.x & value, self.y & value,
                        self.z & value, self.w & value)

    def __rand__(self, value):
        return Vec4(value & self.x, value & self.y, value & self.z, value & self.w)

    def __or__(self, value):
        if isinstance(value, Vec4):
            return Vec4(self.x | value.x, self.y | value.y,
                        self.z | value.z, self.w | value.w)
        else:
            return Vec4(self.x | value, self.y | value,
                        self.z | value, self.w | value)

    def __ror__(self, value):
        return Vec4(value | self.x, value | self.y, value | self.z, value | self.w)

    def __xor__(self, value):
        if isinstance(value, Vec4):
            return Vec4(self.x ^ value.x, self.y ^ value.y,
                        self.z ^ value.z, self.w ^ value.w)
        else:
            return Vec4(self.x ^ value, self.y ^ value,
                        self.z ^ value, self.w ^ value)

    def __rxor__(self, value):
        return Vec4(value ^ self.x, value ^ self.y, value ^ self.z, value ^ self.w)

    def __lshift__(self, value):
        if isinstance(value, Vec4):
            return Vec4(self.x << value.x, self.y << value.y,
                        self.z << value.z, self.w << value.w)
        else:
            return Vec4(self.x << value, self.y << value,
                        self.z << value, self.w << value)

    def __rlshift__(self, value):
        return Vec4(value << self.x, value << self.y,
                    value << self.z, value << self.w)

    def __rshift__(self, value):
        if isinstance(value, Vec4):
            return Vec4(self.x >> value.x, self.y >> value.y,
                        self.z >> value.z, self.w >> value.w)
        else:
            return Vec4(self.x >> value, self.y >> value,
                        self.z >> value, self.w >> value)

    def __rrshift__(self, value):
        return Vec4(value >> self.x, value >> self.y,
                    value >> self.z, value >> self.w)

    def __invert__(self):
        return Vec4(~self.x, ~self.y, ~self.z, ~self.w)

    # def __nonzero__(self):
    #     return self.x == 0 and self.y == 0 and self.z == 0 and self.w == 0

    # def __str__(self):
    #     return "Vec4(%.3f, %.3f, %.3f, %.3f)" % (self.x, self.y, self.z, self.w)
    #
    # __repr__ = __str__

    # implement swizzle,
    # etc, v.xxxx, v.arg, v.qpst
    def __getattribute__(self, name):
        # TODO: implement swizzle for vec2
        if len(name) == 4:
            xyzw = (self.x, self.y, self.z, self.w) * 3
            return Vec4([xyzw['xyzwrgbastpq'.index(i)] for i in name])
        elif len(name) == 3:
            from glm.detail.type_vec3 import Vec3
            xyzw = (self.x, self.y, self.z) * 3
            return Vec3([xyzw['xyzwrgbastpq'.index(i)] for i in name])

        return super(Vec4, self).__getattribute__(name)


class DVec4(Vec4):
    """double type vec4"""
    dataType = 'd'


class IVec4(Vec4):
    """signed int type vec4"""
    dataType = 'i'


class UVec4(Vec4):
    """unsigned int type vec4"""
    dataType = 'I'

