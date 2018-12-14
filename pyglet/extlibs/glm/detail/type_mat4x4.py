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
import sys

from .type_vec4 import Vec4


if sys.version_info > (3, 0):
    long = int


class Mat4x4(object):

    def __init__(self, *args, **kwargs):
        v0 = Vec4(x=1.0)
        v1 = Vec4(y=1.0)
        v2 = Vec4(z=1.0)
        v3 = Vec4(w=1.0)
        if kwargs:
            v0.x = kwargs.get('x0', 0.0)
            v0.y = kwargs.get('y0', 0.0)
            v0.z = kwargs.get('z0', 0.0)
            v0.w = kwargs.get('w0', 0.0)
            v1.x = kwargs.get('x1', 0.0)
            v1.y = kwargs.get('y1', 0.0)
            v1.z = kwargs.get('z1', 0.0)
            v1.w = kwargs.get('w1', 0.0)
            v2.x = kwargs.get('x2', 0.0)
            v2.y = kwargs.get('y2', 0.0)
            v2.z = kwargs.get('z2', 0.0)
            v2.w = kwargs.get('w2', 0.0)
            v3.x = kwargs.get('x3', 0.0)
            v3.y = kwargs.get('y3', 0.0)
            v3.z = kwargs.get('z3', 0.0)
            v3.w = kwargs.get('w3', 0.0)
        elif args:
            lenArgs = len(args)
            if lenArgs == 1:
                m = args[0]
                # TODO: implement argument is mat2x2, mat3x3, ...
                if isinstance(m, Mat4x4):
                    v0 = m[0]
                    v1 = m[1]
                    v2 = m[2]
                    v3 = m[3]
                elif isinstance(m, list) or isinstance(m, tuple):
                    if len(m) != 16:
                        raise TypeError('list or tuple must have 16 items')
                    v0.x = m[0]
                    v1.x = m[1]
                    v2.x = m[2]
                    v3.x = m[3]
                    v0.y = m[4]
                    v1.y = m[5]
                    v2.y = m[6]
                    v3.y = m[7]
                    v0.z = m[8]
                    v1.z = m[9]
                    v2.z = m[10]
                    v3.z = m[11]
                    v0.w = m[12]
                    v1.w = m[13]
                    v2.w = m[14]
                    v3.w = m[15]
                elif isinstance(m, float) or isinstance(m, int) or isinstance(m, long):
                    v0 = Vec4(x=m)
                    v1 = Vec4(y=m)
                    v2 = Vec4(z=m)
                    v3 = Vec4(w=m)
            elif lenArgs == 4:
                if isinstance(args[0], Vec4):
                    v0 = args[0]
                elif isinstance(args[0], list) or isinstance(args[0], tuple):
                    v0 = Vec4(args[0])

                if isinstance(args[1], Vec4):
                    v1 = args[1]
                elif isinstance(args[1], list) or isinstance(args[1], tuple):
                    v1 = Vec4(args[1])

                if isinstance(args[2], Vec4):
                    v2 = args[2]
                elif isinstance(args[2], list) or isinstance(args[2], tuple):
                    v2 = Vec4(args[2])

                if isinstance(args[3], Vec4):
                    v3 = args[3]
                elif isinstance(args[3], list) or isinstance(args[3], tuple):
                    v3 = Vec4(args[3])

        self.__value = [v0, v1, v2, v3]

    def __len__(self):
        return 4

    def __getitem__(self, index):
        if (index < -4) or (index > 3):
            raise IndexError

        if index == 0 or index == -4:
            return self.__value[0]
        elif index == 1 or index == -3:
            return self.__value[1]
        elif index == 2 or index == -2:
            return self.__value[2]
        elif index == 3 or index == -1:
            return self.__value[3]

        return super(Mat4x4, self).__getItem(index)

    def __setitem__(self, index, value):
        if (index < -4) or (index > 3):
            raise IndexError

        if not isinstance(value, Vec4):
            raise TypeError('Must be a Vec4')

        if index == 0 or index == -4:
            self.__value[0] = value
        elif index == 1 or index == -3:
            self.__value[1] = value
        elif index == 2 or index == -2:
            self.__value[2] = value
        elif index == 3 or index == -1:
            self.__value[3] = value

    def __iadd__(self, value):
        if isinstance(value, Mat4x4):
            self.__value[0] += value[0]
            self.__value[1] += value[1]
            self.__value[2] += value[2]
            self.__value[3] += value[3]
        else:
            self.__value[0] += value
            self.__value[1] += value
            self.__value[2] += value
            self.__value[3] += value
        return self

    def __isub__(self, value):
        if isinstance(value, Mat4x4):
            self.__value[0] -= value[0]
            self.__value[1] -= value[1]
            self.__value[2] -= value[2]
            self.__value[3] -= value[3]
        else:
            self.__value[0] -= value
            self.__value[1] -= value
            self.__value[2] -= value
            self.__value[3] -= value
        return self

    def __imul__(self, value):
        if isinstance(value, Mat4x4):
            self.__value[0] *= value[0]
            self.__value[1] *= value[1]
            self.__value[2] *= value[2]
            self.__value[3] *= value[3]
        else:
            self.__value[0] *= value
            self.__value[1] *= value
            self.__value[2] *= value
            self.__value[3] *= value
        return self

    def __idiv__(self, value):
        if isinstance(value, Mat4x4):
#             self.__value[0] /= value[0]
#             self.__value[1] /= value[1]
#             self.__value[2] /= value[2]
#             self.__value[3] /= value[3]
            self *= Mat4x4.compute_inverse(value)
        else:
            self.__value[0] /= value
            self.__value[1] /= value
            self.__value[2] /= value
            self.__value[3] /= value
        return self

    __itruediv__ = __idiv__

    @staticmethod
    def compute_inverse(m):
        coef00 = m[2][2] * m[3][3] - m[3][2] * m[2][3]
        coef02 = m[1][2] * m[3][3] - m[3][2] * m[1][3]
        coef03 = m[1][2] * m[2][3] - m[2][2] * m[1][3]

        coef04 = m[2][1] * m[3][3] - m[3][1] * m[2][3]
        coef06 = m[1][1] * m[3][3] - m[3][1] * m[1][3]
        coef07 = m[1][1] * m[2][3] - m[2][1] * m[1][3]

        coef08 = m[2][1] * m[3][2] - m[3][1] * m[2][2]
        coef10 = m[1][1] * m[3][2] - m[3][1] * m[1][2]
        coef11 = m[1][1] * m[2][2] - m[2][1] * m[1][2]

        coef12 = m[2][0] * m[3][3] - m[3][0] * m[2][3]
        coef14 = m[1][0] * m[3][3] - m[3][0] * m[1][3]
        coef15 = m[1][0] * m[2][3] - m[2][0] * m[1][3]

        coef16 = m[2][0] * m[3][2] - m[3][0] * m[2][2]
        coef18 = m[1][0] * m[3][2] - m[3][0] * m[1][2]
        coef19 = m[1][0] * m[2][2] - m[2][0] * m[1][2]

        coef20 = m[2][0] * m[3][1] - m[3][0] * m[2][1]
        coef22 = m[1][0] * m[3][1] - m[3][0] * m[1][1]
        coef23 = m[1][0] * m[2][1] - m[2][0] * m[1][1]

        fac0 = Vec4(coef00, coef00, coef02, coef03)
        fac1 = Vec4(coef04, coef04, coef06, coef07)
        fac2 = Vec4(coef08, coef08, coef10, coef11)
        fac3 = Vec4(coef12, coef12, coef14, coef15)
        fac4 = Vec4(coef16, coef16, coef18, coef19)
        fac5 = Vec4(coef20, coef20, coef22, coef23)

        v0 = Vec4(m[1][0], m[0][0], m[0][0], m[0][0])
        v1 = Vec4(m[1][1], m[0][1], m[0][1], m[0][1])
        v2 = Vec4(m[1][2], m[0][2], m[0][2], m[0][2])
        v3 = Vec4(m[1][3], m[0][3], m[0][3], m[0][3])

        inv0 = Vec4(v1 * fac0 - v2 * fac1 + v3 * fac2)
        inv1 = Vec4(v0 * fac0 - v2 * fac3 + v3 * fac4)
        inv2 = Vec4(v0 * fac1 - v1 * fac3 + v3 * fac5)
        inv3 = Vec4(v0 * fac2 - v1 * fac4 + v2 * fac5)

        signA = Vec4(1, -1, 1, -1)
        signB = Vec4(-1, 1, -1, 1)
        inverse = Mat4x4(inv0 * signA, inv1 * signB, inv2 * signA, inv3 * signB)

        row0 = Vec4(inverse[0][0], inverse[1][0], inverse[2][0], inverse[3][0])

        dot0 = Vec4(m[0] * row0)
        dot1 = (dot0.x + dot0.y) + (dot0.z + dot0.w)

        oneOverDeteminant = 1 / dot1

        return inverse * oneOverDeteminant

    # Binary operators
    def __add__(self, value):
        if isinstance(value, Mat4x4):
            return Mat4x4(self.__value[0] + value[0], self.__value[1] + value[1],
                          self.__value[2] + value[2], self.__value[3] + value[3])
        else:
            return Mat4x4(self.__value[0] + value, self.__value[1] + value,
                          self.__value[2] + value, self.__value[3] + value)

    def __radd__(self, value):
        return Mat4x4(self.__value[0] + value, self.__value[1] + value,
                      self.__value[2] + value, self.__value[3] + value)

    def __sub__(self, value):
        if isinstance(value, Mat4x4):
            return Mat4x4(self.__value[0] - value[0], self.__value[1] - value[1],
                          self.__value[2] - value[2], self.__value[3] - value[3])
        else:
            return Mat4x4(self.__value[0] - value, self.__value[1] - value,
                          self.__value[2] - value, self.__value[3] - value)

    def __rsub__(self, value):
        return Mat4x4(value - self.__value[0], value - self.__value[1],
                      value - self.__value[2], value - self.__value[3])

    def __mul__(self, value):
        result = Mat4x4(0.)
        if isinstance(value, Mat4x4):
            srcA0 = self.__value[0]
            srcA1 = self.__value[1]
            srcA2 = self.__value[2]
            srcA3 = self.__value[3]

            srcB0 = value[0]
            srcB1 = value[1]
            srcB2 = value[2]
            srcB3 = value[3]

            result[0] = srcA0 * srcB0[0] + srcA1 * srcB0[1] + srcA2 * srcB0[2] + srcA3 * srcB0[3]
            result[1] = srcA0 * srcB1[0] + srcA1 * srcB1[1] + srcA2 * srcB1[2] + srcA3 * srcB1[3]
            result[2] = srcA0 * srcB2[0] + srcA1 * srcB2[1] + srcA2 * srcB2[2] + srcA3 * srcB2[3]
            result[3] = srcA0 * srcB3[0] + srcA1 * srcB3[1] + srcA2 * srcB3[2] + srcA3 * srcB3[3]
        elif isinstance(value, float) or isinstance(value, int) or isinstance(value, long):
            result[0] = self.__value[0] * value
            result[1] = self.__value[1] * value
            result[2] = self.__value[2] * value
            result[3] = self.__value[3] * value
        elif isinstance(value, Vec4):
            mov0 = Vec4(value[0])
            mov1 = Vec4(value[1])
            mul0 = self.__value[0] * mov0
            mul1 = self.__value[1] * mov1
            add0 = Vec4(mul0 - mul1)
            mov2 = Vec4(value[2])
            mov3 = Vec4(value[3])
            mul2 = self.__value[2] * mov2
            mul3 = self.__value[3] * mov3
            add1 = mul2 + mul3
            add2 = add0 + add1
            return add2
        # TODO: support mat2x2, mat3x3
        return result

    def __rmul__(self, value):
        if isinstance(value, float) or isinstance(value, int) or isinstance(value, long):
            result = Mat4x4(0.)
            result[0] = self.__value[0] * value
            result[1] = self.__value[1] * value
            result[2] = self.__value[2] * value
            result[3] = self.__value[3] * value
            return result
        elif isinstance(value, Vec4):
            return Vec4(self.__value[0][0] * value[0] + self.__value[0][1] * value[1] + self.__value[0][2] * value[2] + self.__value[0][3] * value[3],
                        self.__value[1][0] * value[0] + self.__value[1][1] * value[1] + self.__value[1][2] * value[2] + self.__value[1][3] * value[3],
                        self.__value[2][0] * value[0] + self.__value[2][1] * value[1] + self.__value[2][2] * value[2] + self.__value[2][3] * value[3],
                        self.__value[3][0] * value[0] + self.__value[3][1] * value[1] + self.__value[3][2] * value[2] + self.__value[3][3] * value[3])

    __matmul__ = __mul__
    __rmatmul__ = __rmul__

    def __div__(self, value):
        if isinstance(value, float) or isinstance(value, int) or isinstance(value, long):
            return Mat4x4(self.__value[0] / value, self.__value[1] / value,
                          self.__value[2] / value, self.__value[3] / value)
        elif isinstance(value, Vec4):
            return Mat4x4.compute_inverse(self) * value
        elif isinstance(value, Mat4x4):
            result = Mat4x4(self)
            result /= value
            return result

    def __rdiv__(self, value):
        if isinstance(value, float) or isinstance(value, int) or isinstance(value, long):
            return Mat4x4(value / self.__value[0], value / self.__value[1],
                          value / self.__value[2], value / self.__value[3])
        elif isinstance(value, Vec4):
            return value * Mat4x4.compute_inverse(self)

    __truediv__ = __div__
    __rtruediv__ = __rdiv__

    def __neg__(self):
        return Mat4x4(-self.__value[0], -self.__value[1],
                      -self.__value[2], -self.__value[3])

    def __eq__(self, other):
        return self.__value[0] == other[0] and self.__value[1] == other[1] and self.__value[2] == other[2] and self.__value[3] == other[3]

    def __neq__(self, other):
        return self.__value[0] != other[0] and self.__value[1] != other[1] and self.__value[2] != other[2] and self.__value[3] != other[3]

    def __iter__(self):
        return iter((self.__value[0].x, self.__value[1].x, self.__value[2].x, self.__value[3].x,
                     self.__value[0].y, self.__value[1].y, self.__value[2].y, self.__value[3].y,
                     self.__value[0].z, self.__value[1].z, self.__value[2].z, self.__value[3].z,
                     self.__value[0].w, self.__value[1].w, self.__value[2].w, self.__value[3].w))

    def __repr__(self):
        return "{0}\n{1}\n{2}\n{3}".format(*self.__value)
