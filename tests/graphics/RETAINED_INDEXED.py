#!/usr/bin/env python
"""Tests vertex list drawing using indexed data.
"""
import unittest

import pyglet

from graphics_common import GraphicsIndexedGenericTestCase, get_feedback, GL_TRIANGLES

__noninteractive = True


class GraphicsIndexedVertexListTestCase(GraphicsIndexedGenericTestCase, unittest.TestCase):
    def get_feedback(self, data):
        vertex_list = pyglet.graphics.vertex_list_indexed(self.n_vertices, self.index_data, *data)
        return get_feedback(lambda: vertex_list.draw(GL_TRIANGLES))

if __name__ == '__main__':
    unittest.main()
