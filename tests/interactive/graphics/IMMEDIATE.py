#!/usr/bin/env python
"""Tests immediate drawing.
"""
import unittest

import pyglet

from graphics_common import GraphicsGenericTestCase, get_feedback, GL_TRIANGLES

__noninteractive = True


class GraphicsImmediateTestCase(GraphicsGenericTestCase, unittest.TestCase):
    def get_feedback(self, data):
        return get_feedback(lambda: pyglet.graphics.draw(self.n_vertices, GL_TRIANGLES, *data))

if __name__ == '__main__':
    unittest.main()
