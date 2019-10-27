#!/usr/bin/env python
"""Tests vertex list drawing.
"""
import unittest

import pyglet

from tests.annotations import Platform, skip_platform
from .graphics_common import GraphicsGenericTestCase, get_feedback, GL_TRIANGLES


@skip_platform(Platform.OSX)  # TODO: Check whether OpenGL < 3.0 or compatibility profile is enabled
class RetainedDrawingTestCase(GraphicsGenericTestCase, unittest.TestCase):
    def get_feedback(self, data):
        vertex_list = pyglet.graphics.vertex_list(self.n_vertices, *data)
        return get_feedback(lambda: vertex_list.draw(GL_TRIANGLES))

