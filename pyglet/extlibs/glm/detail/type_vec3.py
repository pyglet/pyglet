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


class Vec3(type_vec.BaseVec3):

    def __new__(cls, *args, **kwargs):
        inList = []
        if kwargs:
            inList.append(kwargs.get('x', 0))
            inList.append(kwargs.get('y', 0))
            inList.append(kwargs.get('z', 0))
        elif args:
            argsLen = len(args)
            if argsLen == 1:
                arg0 = args[0]
                if isinstance(arg0, type_vec.BaseVec4):
                    inList = arg0.tolist()[:3]
                elif isinstance(arg0, type_vec.BaseVec3):
                    inList = arg0.tolist()
                elif isinstance(arg0, type_vec.BaseVec2):
                    inList = arg0.tolist() + [0]
                elif isinstance(arg0, type_vec.BaseVec1):
                    inList = arg0.tolist() + [0, 0]
                elif isinstance(arg0, list) or isinstance(arg0, tuple):
                    il = []
                    arg0Len = len(arg0)
                    if arg0Len == 1:
                        il = list(arg0) + [0, 0]
                    elif arg0Len == 2:
                        il = list(arg0) + [0]
                    elif arg0Len == 3:
                        il = list(arg0)
                    inList = il
                elif isinstance(arg0, numbers.Number):
                    inList = [arg0, arg0, arg0]
            elif argsLen == 2:
                arg0, arg1 = args
                if isinstance(arg0, type_vec.BaseVec2) and isinstance(arg1, numbers.Number):
                    inList = arg0.tolist() + [arg1]
                elif isinstance(arg0, numbers.Number) and isinstance(arg1, type_vec.BaseVec2):
                    inList = [arg0] + arg1.tolist()
                elif isinstance(arg0, numbers.Number) and isinstance(arg1, numbers.Number):
                    inList = [arg0, arg1, 0]
            elif argsLen == 3:
                inList = args
            else:
                inList = args[:3]
        if not args and not kwargs:
            inList = [0, 0, 0]

        return type_vec.BaseVec3.__new__(cls, Vec3.dataType, inList)

    def __add__(self, value):
        if isinstance(value, Vec3):
            return Vec3(self.x + value.x, self.y + value.y, self.z + value.z)
        else:
            return Vec3(self.x + value, self.y + value, self.z + value)

    def __radd__(self, value):
        return Vec3(value + self.x, value + self.y, value + self.z)

    def __sub__(self, value):
        if isinstance(value, Vec3):
            return Vec3(self.x - value.x, self.y - value.y, self.z - value.z)
        else:
            return Vec3(self.x - value, self.y - value, self.z - value)

    def __rsub__(self, value):
        return Vec3(value - self.x, value - self.y, value - self.z)

    def __mul__(self, value):
        if isinstance(value, Vec3):
            return Vec3(self.x * value.x, self.y * value.y, self.z * value.z)
        else:
            return Vec3(self.x * value, self.y * value, self.z * value)

    def __rmul__(self, value):
        return Vec3(value * self.x, value * self.y, value * self.z)

    def __div__(self, value):
        if isinstance(value, Vec3):
            return Vec3(self.x / value.x, self.y / value.y, self.z / value.z)
        else:
            return Vec3(self.x / value, self.y / value, self.z / value)

    def __rdiv__(self, value):
        return Vec3(value / self.x, value / self.y, value / self.z)

    def __truediv__(self, value):
        if isinstance(value, Vec3):
            return Vec3(self.x / float(value.x), self.y / float(value.y), self.z / float(value.z))
        else:
            return Vec3(self.x / float(value), self.y / float(value), self.z / float(value))

    def __rtruediv__(self, value):
        v = float(value)
        return Vec3(v / self.x, v / self.y, v / self.z)

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def __mod__(self, value):
        if isinstance(value, Vec3):
            return Vec3(self.x % value.x, self.y % value.y, self.z % value.z)
        else:
            return Vec3(self.x % value, self.y % value, self.z % value)

    def __rmod__(self, value):
        return Vec3(value % self.x, value % self.y, value % self.z)

    def __and__(self, value):
        if isinstance(value, Vec3):
            return Vec3(self.x & value.x, self.y & value.y, self.z & value.z)
        else:
            return Vec3(self.x & value, self.y & value, self.z & value)

    def __rand__(self, value):
        return Vec3(value & self.x, value & self.y, value & self.z)

    def __or__(self, value):
        if isinstance(value, Vec3):
            return Vec3(self.x | value.x, self.y | value.y, self.z | value.z)
        else:
            return Vec3(self.x | value, self.y | value, self.z | value)

    def __ror__(self, value):
        return Vec3(value | self.x, value | self.y, value | self.z)

    def __xor__(self, value):
        if isinstance(value, Vec3):
            return Vec3(self.x ^ value.x, self.y ^ value.y, self.z ^ value.z)
        else:
            return Vec3(self.x ^ value, self.y ^ value, self.z ^ value)

    def __rxor__(self, value):
        return Vec3(value ^ self.x, value ^ self.y, value ^ self.z)

    def __lshift__(self, value):
        if isinstance(value, Vec3):
            return Vec3(self.x << value.x, self.y << value.y, self.z << value.z)
        else:
            return Vec3(self.x << value, self.y << value, self.z << value)

    def __rlshift__(self, value):
        return Vec3(value << self.x, value << self.y, value << self.z)

    def __rshift__(self, value):
        if isinstance(value, Vec3):
            return Vec3(self.x >> value.x, self.y >> value.y, self.z >> value.z)
        else:
            return Vec3(self.x >> value, self.y >> value, self.z >> value)

    def __rrshift__(self, value):
        return Vec3(value >> self.x, value >> self.y, value >> self.z)

    def __invert__(self):
        return Vec3(~self.x, ~self.y, ~self.z)

    # def __nonzero__(self):
    #     return self.x == 0 and self.y == 0 and self.z == 0
    #
    # def __str__(self):
    #     return "Vec3(%.3f, %.3f, %.3f)" % (self.x, self.y, self.z)
    #
    # __repr__ = __str__

    # implement swizzle,
    # etc, v.xxx, v.ar, v.qps
    def __getattribute__(self, name):
        if len(name) == 3:
            xyzw = (self.x, self.y, self.z) * 3
            return Vec3([xyzw['xyzrgbstp'.index(i)] for i in name])
        elif len(name) == 4:
            from glm.detail.type_vec4 import Vec4
            xyzw = (self.x, self.y, self.z) * 3
            return Vec4([xyzw['xyzrgbstp'.index(i)] for i in name])

        return super(Vec3, self).__getattribute__(name)


class DVec3(Vec3):
    """double type vec3"""
    dataType = 'd'


class IVec3(Vec3):
    """signed int type vec3"""
    dataType = 'i'


class UVec3(Vec3):
    """unsigned int type vec3"""
    dataType = 'I'

