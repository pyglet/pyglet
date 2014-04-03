#!/usr/bin/env python

from abc import abstractmethod
import random
from collections import deque

from pyglet.gl import *


# http://stackoverflow.com/a/312464/931303
def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def get_feedback(func):
    feedback_buffer = (GLfloat * 8096)()
    # Project in clip coords
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, 1, 0, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glFeedbackBuffer(len(feedback_buffer), GL_4D_COLOR_TEXTURE, feedback_buffer)
    glRenderMode(GL_FEEDBACK)
    func()
    size = glRenderMode(GL_RENDER)
    buffer = feedback_buffer[:size]
    vertices = []
    colors = []
    tex_coords = []
    while buffer:
        token = int(buffer.pop(0))
        assert token == GL_POLYGON_TOKEN
        n = int(buffer.pop(0))
        for i in range(n):
            vertices.extend(buffer[:4])
            colors.extend(buffer[4:8])
            tex_coords.extend(buffer[8:12])
            del buffer[:12]

    return vertices, colors, tex_coords


class GraphicsGenericTestCase:
    """
    A generic test for asserting vertices positions
    using openGL Feedback Buffer.
    This is not really a testcase because it cannot be
    tested alone. Use it by subclassing it
    with unittest.TestCase.

    It has one abstract method that the subclass must
    overwrite.
    """

    def setUp(self):
        # has to be a multiple of 3 because of the Feedback buffer.
        # has to be a multiple of 2 because of indexed data subclass.
        self.n_vertices = 36
        self.v3f_data = [v/float(self.n_vertices*3) for v in range(self.n_vertices * 3)]
        self.v2f_data = [v/float(self.n_vertices*2) for v in range(self.n_vertices * 2)]
        self.c4f_data = [v/float(self.n_vertices*4) for v in range(self.n_vertices * 4)]
        self.c3f_data = [v/float(self.n_vertices*3) for v in range(self.n_vertices * 3)]
        self.t4f_data = [v/float(self.n_vertices*4) for v in range(self.n_vertices * 4)]
        self.t3f_data = [v/float(self.n_vertices*3) for v in range(self.n_vertices * 3)]
        self.t2f_data = [v/float(self.n_vertices*2) for v in range(self.n_vertices * 2)]

    @staticmethod
    def _are_equal(expected, result):
        """
        Compares that two lists are equal within an error.
        Returns True if they are equal and False otherwise.
        """
        for e, r in zip(expected, result):
            if abs(e - r) > 0.01:
                return False
        return True

    def _are_equal_within_rotation(self, expected, result_chunk):
        """
        Checks that two lists of expected and result are equal
        within a rotation and a small error.
        Returns true if they are equal and False otherwise.
        """
        rotation_deque = deque(result_chunk)
        for rotation in range(3):  # triangles require at most 3 rotations
            rotation_deque.rotate(4)  # because it has 4 components.
            result = list(rotation_deque)[:2]  # we only test x and y

            if self._are_equal(expected, result):
                return True

        return False

    def check(self, expected, result, dimensions):
        """
        Asserts that the result is equivalent to the expected result.
        """
        if len(expected) != len(result) * dimensions / 4:
            self.fail('Incorrect number of vertices in feedback array: '
                      'expected: %d, obtained: %d' % (len(expected), len(result) * dimensions / 4))

        # there are two factors here:
        # 1. there are several triangles and their out-order can be different from in-order.
        # 2. in each triangle, the out-order of the vertices can be a rotation from its in-order.

        # to tackle 1:
        # we divide the result and the expected in chunks, each representing one triangle,
        # and we compare each triangle individually.

        # to tackle 2:
        # within each triangle, we cycle the vertices list and check if any rotation matches the expected.

        # for each triangle in the expected
        for e_chunk in chunks(expected, dimensions):
            expected_chunk = e_chunk[0:2]  # we only test x and y

            # for each triangle in the result (tackling 1.)
            # notice that result always has 4 dimensions: (x, y, z, z-buffer).
            was_found = False
            for result_chunk in chunks(result, 3*4):
                # here we tackle 2.
                if self._are_equal_within_rotation(expected_chunk, result_chunk):
                    was_found = True
                    break
            # we assert that every triangle must be matched.
            self.assertTrue(was_found)

    @abstractmethod
    def get_feedback(self, data):
        pass

    def get_data(self, data, _):
        """
        Used for pos-processing of the expected result.
        See subclass.
        """
        return data

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
        vertices, colors, tex_coords = self.get_feedback(data)

        self.check(self.get_data(v_data, n_v), vertices, n_v)
        if c_fmt:
            self.check(self.get_data(c_data, n_c), colors, n_c)
        if t_fmt:
            self.check(self.get_data(t_data, n_t), tex_coords, n_t)

    def test_v2f(self):
        self.generic_test('v2f', self.v2f_data)

    def test_v3f(self):
        self.generic_test('v3f', self.v3f_data)

    def test_v2f_c3f(self):
        self.generic_test('v2f', self.v2f_data, 'c3f', self.c3f_data)

    def test_v2f_c4f(self):
        self.generic_test('v2f', self.v2f_data, 'c4f', self.c4f_data)

    def test_v3f_c3f(self):
        self.generic_test('v3f', self.v3f_data, 'c3f', self.c3f_data)

    def test_v3f_c4f(self):
        self.generic_test('v3f', self.v3f_data, 'c4f', self.c4f_data)

    def test_v2f_t2f(self):
        self.generic_test('v2f', self.v2f_data, None, None, 't2f', self.t2f_data)

    def test_v3f_c3f_t2f(self):
        self.generic_test('v3f', self.v3f_data, 'c3f', self.c3f_data, 't2f', self.t2f_data)

    def test_v3f_c3f_t3f(self):
        self.generic_test('v3f', self.v3f_data, 'c3f', self.c3f_data, 't3f', self.t3f_data)

    def test_v3f_c4f_t4f(self):
        self.generic_test('v3f', self.v3f_data, 'c4f', self.c4f_data, 't4f', self.t4f_data)


class GraphicsIndexedGenericTestCase(GraphicsGenericTestCase):
    """
    A generic test for asserting vertices positions
    using openGL Feedback Buffer and indexed data.

    It has one abstract method that the subclass must
    overwrite.
    """
    def setUp(self):
        GraphicsGenericTestCase.setUp(self)

        # we use half of the data so we repeat vertices.
        self.index_data = range(self.n_vertices//2) * 2
        random.seed(1)
        random.shuffle(self.index_data)

    def get_data(self, data, dimensions):
        """
        Reorders data according to the indexing.
        """
        ordered = []
        for i in self.index_data:
            ordered.extend(data[i * dimensions:(i+1)*dimensions])
        return ordered
