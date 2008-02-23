#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet

from graphics_common import *

__noninteractive = True

class TEST_CASE(unittest.TestCase):
    def check(self, expected, result, dimensions):
        if len(expected) != len(result) * dimensions / 4:
            self.fail('Incorrect number of vertices in feedback array')
        for d in range(2):
            for e, r in zip(expected[d::dimensions], result[d::4]):
                if abs(e - r) > 0.01:
                    self.fail('Feedback array is in error: %r, %r' % \
                        (e, r))

    def generic_test(self, v_fmt, v_data, 
                     c_fmt=None, c_data=None, 
                     t_fmt=None, t_data=None):
        data = [(v_fmt, v_data)]
        n_v = int(v_fmt[1])
        if c_fmt:
            data.append((c_fmt, c_data))
            n_c = int(c_fmt[1])
        if t_fmt:
            data.append((t_fmt, t_data))
            n_t = int(t_fmt[1])
        vertices, colors, tex_coords = get_feedback(lambda: \
            pyglet.graphics.draw_indexed(n_vertices, GL_TRIANGLES, index_data, 
                                         *data))
        self.check(get_ordered_data(v_data, n_v), vertices, n_v)
        if c_fmt:
            self.check(get_ordered_data(c_data, n_c), colors, n_c)
        if t_fmt:
            self.check(get_ordered_data(t_data, n_t), tex_coords, n_t)

    def test_v2f(self):
        self.generic_test('v2f', v2f_data)

    def test_v3f(self):
        self.generic_test('v3f', v3f_data)

    def test_v2f_c3f(self):
        self.generic_test('v2f', v2f_data, 'c3f', c3f_data)

    def test_v2f_c4f(self):
        self.generic_test('v2f', v2f_data, 'c4f', c4f_data)

    def test_v3f_c3f(self):
        self.generic_test('v3f', v3f_data, 'c3f', c3f_data)

    def test_v3f_c4f(self):
        self.generic_test('v3f', v3f_data, 'c4f', c4f_data)

    def test_v2f_t2f(self):
        self.generic_test('v2f', v2f_data, None, None, 't2f', t2f_data)

    def test_v3f_c3f_t2f(self):
        self.generic_test('v3f', v3f_data, 'c3f', c3f_data, 't2f', t2f_data)

    def test_v3f_c3f_t3f(self):
        self.generic_test('v3f', v3f_data, 'c3f', c3f_data, 't3f', t3f_data)

    def test_v3f_c4f_t4f(self):
        self.generic_test('v3f', v3f_data, 'c4f', c4f_data, 't4f', t4f_data)

if __name__ == '__main__':
    unittest.main()
