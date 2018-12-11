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

import array


class BaseVec1(array.array):

    dataType = 'f'

    def __new__(cls, dataType, data):
        return array.array.__new__(cls, dataType, data)

    @property
    def x(self):
        return self.__getitem__(0)

    @x.setter
    def x(self, v):
        self.__setitem__(0, v)

    r = x
    s = r

    @property
    def nbytes(self):
        return self.buffer_info()[1] * self.itemsize

    def __iadd__(self, value):
        if isinstance(value, self.__class__):
            self.x += value.x
        else:
            self.x += value
        return self

    def __isub__(self, value):
        if isinstance(value, self.__class__):
            self.x -= value.x
        else:
            self.x -= value
        return self

    def __imul__(self, value):
        if isinstance(value, self.__class__):
            self.x *= value.x
        else:
            self.x *= value
        return self

    def __idiv__(self, value):
        if isinstance(value, self.__class__):
            self.x /= value.x
        else:
            self.x /= value
        return self

    def __itruediv__(self, value):
        if isinstance(value, self.__class__):
            self.x /= value.x
        else:
            self.x /= value
        return self

    def __imod__(self, value):
        if isinstance(value, self.__class__):
            self.x %= value.x
        else:
            self.x %= value
        return self

    def __iand__(self, value):
        if isinstance(value, self.__class__):
            self.x &= value.x
        else:
            self.x &= value
        return self

    def __ior__(self, value):
        if isinstance(value, self.__class__):
            self.x |= value.x
        else:
            self.x |= value
        return self

    def __ixor__(self, value):
        if isinstance(value, self.__class__):
            self.x ^= value.x
        else:
            self.x ^= value
        return self

    def __ilshift__(self, value):
        if isinstance(value, self.__class__):
            self.x <<= value.x
        else:
            self.x <<= value
        return self

    def __irshift__(self, value):
        if isinstance(value, self.__class__):
            self.x >>= value.x
        else:
            self.x >>= value
        return self

    def __eq__(self, other):
        return self.x == other.x

    def __ne__(self, other):
        return self.x != other.x

class BaseVec2(BaseVec1):

    def __new__(cls, dataType, data):
        return BaseVec1.__new__(cls, dataType, data)

    @property
    def y(self):
        return self.__getitem__(1)

    @y.setter
    def y(self, v):
        self.__setitem__(1, v)

    g = y
    t = g

    def __iadd__(self, value):
        if isinstance(value, self.__class__):
            self.x += value.x
            self.y += value.y
        else:
            self.x += value
            self.y += value
        return self

    def __isub__(self, value):
        if isinstance(value, self.__class__):
            self.x -= value.x
            self.y -= value.y
        else:
            self.x -= value
            self.y -= value
        return self

    def __imul__(self, value):
        if isinstance(value, self.__class__):
            self.x *= value.x
            self.y *= value.y
        else:
            self.x *= value
            self.y *= value
        return self

    def __idiv__(self, value):
        if isinstance(value, self.__class__):
            self.x /= value.x
            self.y /= value.y
        else:
            self.x /= value
            self.y /= value
        return self

    def __itruediv__(self, value):
        if isinstance(value, self.__class__):
            self.x /= value.x
            self.y /= value.y
        else:
            self.x /= value
            self.y /= value
        return self

    def __imod__(self, value):
        if isinstance(value, self.__class__):
            self.x %= value.x
            self.y %= value.y
        else:
            self.x %= value
            self.y %= value
        return self

    def __iand__(self, value):
        if isinstance(value, self.__class__):
            self.x &= value.x
            self.y &= value.y
        else:
            self.x &= value
            self.y &= value
        return self

    def __ior__(self, value):
        if isinstance(value, self.__class__):
            self.x |= value.x
            self.y |= value.y
        else:
            self.x |= value
            self.y |= value
        return self

    def __ixor__(self, value):
        if isinstance(value, self.__class__):
            self.x ^= value.x
            self.y ^= value.y
        else:
            self.x ^= value
            self.y ^= value
        return self

    def __ilshift__(self, value):
        if isinstance(value, self.__class__):
            self.x <<= value.x
            self.y <<= value.y
        else:
            self.x <<= value
            self.y <<= value
        return self

    def __irshift__(self, value):
        if isinstance(value, self.__class__):
            self.x >>= value.x
            self.y >>= value.y
        else:
            self.x >>= value
            self.y >>= value
        return self

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.x != other.x and self.y != other.y

class BaseVec3(BaseVec2):
    def __new__(cls, dataType, data):
        return BaseVec2.__new__(cls, dataType, data)

    @property
    def z(self):
        return self.__getitem__(2)

    @z.setter
    def z(self, v):
        self.__setitem__(2, v)

    b = z
    p = b

    def __iadd__(self, value):
        if isinstance(value, self.__class__):
            self.x += value.x
            self.y += value.y
            self.z += value.z
        else:
            self.x += value
            self.y += value
            self.z += value
        return self

    def __isub__(self, value):
        if isinstance(value, self.__class__):
            self.x -= value.x
            self.y -= value.y
            self.z -= value.z
        else:
            self.x -= value
            self.y -= value
            self.z -= value
        return self

    def __imul__(self, value):
        if isinstance(value, self.__class__):
            self.x *= value.x
            self.y *= value.y
            self.z *= value.z
        else:
            self.x *= value
            self.y *= value
            self.z *= value
        return self

    def __idiv__(self, value):
        if isinstance(value, self.__class__):
            self.x /= value.x
            self.y /= value.y
            self.z /= value.z
        else:
            self.x /= value
            self.y /= value
            self.z /= value
        return self

    def __itruediv__(self, value):
        if isinstance(value, self.__class__):
            self.x /= value.x
            self.y /= value.y
            self.z /= value.z
        else:
            self.x /= value
            self.y /= value
            self.z /= value
        return self

    def __imod__(self, value):
        if isinstance(value, self.__class__):
            self.x %= value.x
            self.y %= value.y
            self.z %= value.z
        else:
            self.x %= value
            self.y %= value
            self.z %= value
        return self

    def __iand__(self, value):
        if isinstance(value, self.__class__):
            self.x &= value.x
            self.y &= value.y
            self.z &= value.z
        else:
            self.x &= value
            self.y &= value
            self.z &= value
        return self

    def __ior__(self, value):
        if isinstance(value, self.__class__):
            self.x |= value.x
            self.y |= value.y
            self.z |= value.z
        else:
            self.x |= value
            self.y |= value
            self.z |= value
        return self

    def __ixor__(self, value):
        if isinstance(value, self.__class__):
            self.x ^= value.x
            self.y ^= value.y
            self.z ^= value.z
        else:
            self.x ^= value
            self.y ^= value
            self.z ^= value
        return self

    def __ilshift__(self, value):
        if isinstance(value, self.__class__):
            self.x <<= value.x
            self.y <<= value.y
            self.z <<= value.z
        else:
            self.x <<= value
            self.y <<= value
            self.z <<= value
        return self

    def __irshift__(self, value):
        if isinstance(value, self.__class__):
            self.x >>= value.x
            self.y >>= value.y
            self.z >>= value.z
        else:
            self.x >>= value
            self.y >>= value
            self.z >>= value
        return self

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __ne__(self, other):
        return self.x != other.x and self.y != other.y and self.z != other.z

class BaseVec4(BaseVec3):
    def __new__(cls, dataType, data):
        return BaseVec3.__new__(cls, dataType, data)

    @property
    def w(self):
        return self.__getitem__(3)

    @w.setter
    def w(self, v):
        self.__setitem__(3, v)

    a = w
    q = a

    def __iadd__(self, value):
        if isinstance(value, self.__class__):
            self.x += value.x
            self.y += value.y
            self.z += value.z
            self.w += value.w
        else:
            self.x += value
            self.y += value
            self.z += value
            self.w += value
        return self

    def __isub__(self, value):
        if isinstance(value, self.__class__):
            self.x -= value.x
            self.y -= value.y
            self.z -= value.z
            self.w -= value.w
        else:
            self.x -= value
            self.y -= value
            self.z -= value
            self.w -= value
        return self

    def __imul__(self, value):
        if isinstance(value, self.__class__):
            self.x *= value.x
            self.y *= value.y
            self.z *= value.z
            self.w *= value.w
        else:
            self.x *= value
            self.y *= value
            self.z *= value
            self.w *= value
        return self

    def __idiv__(self, value):
        if isinstance(value, self.__class__):
            self.x /= value.x
            self.y /= value.y
            self.z /= value.z
            self.w /= value.w
        else:
            self.x /= value
            self.y /= value
            self.z /= value
            self.w /= value
        return self

    def __itruediv__(self, value):
        if isinstance(value, self.__class__):
            self.x /= value.x
            self.y /= value.y
            self.z /= value.z
            self.w /= value.w
        else:
            self.x /= value
            self.y /= value
            self.z /= value
            self.w /= value
        return self

    def __imod__(self, value):
        if isinstance(value, self.__class__):
            self.x %= value.x
            self.y %= value.y
            self.z %= value.z
            self.w %= value.w
        else:
            self.x %= value
            self.y %= value
            self.z %= value
            self.w %= value
        return self

    def __iand__(self, value):
        if isinstance(value, self.__class__):
            self.x &= value.x
            self.y &= value.y
            self.z &= value.z
            self.w &= value.w
        else:
            self.x &= value
            self.y &= value
            self.z &= value
            self.w &= value
        return self

    def __ior__(self, value):
        if isinstance(value, self.__class__):
            self.x |= value.x
            self.y |= value.y
            self.z |= value.z
            self.w |= value.w
        else:
            self.x |= value
            self.y |= value
            self.z |= value
            self.w |= value
        return self

    def __ixor__(self, value):
        if isinstance(value, self.__class__):
            self.x ^= value.x
            self.y ^= value.y
            self.z ^= value.z
            self.w ^= value.w
        else:
            self.x ^= value
            self.y ^= value
            self.z ^= value
            self.w ^= value
        return self

    def __ilshift__(self, value):
        if isinstance(value, self.__class__):
            self.x <<= value.x
            self.y <<= value.y
            self.z <<= value.z
            self.w <<= value.w
        else:
            self.x <<= value
            self.y <<= value
            self.z <<= value
            self.w <<= value
        return self

    def __irshift__(self, value):
        if isinstance(value, self.__class__):
            self.x >>= value.x
            self.y >>= value.y
            self.z >>= value.z
            self.w >>= value.w
        else:
            self.x >>= value
            self.y >>= value
            self.z >>= value
            self.w >>= value
        return self

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z and self.w == other.w

    def __ne__(self, other):
        return self.x != other.x and self.y != other.y and self.z != other.z and self.w != other.w

