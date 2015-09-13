#!/usr/bin/env python
"""Tests vertex list drawing using indexed data.
"""
from __future__ import absolute_import
import unittest

import pyglet

from tests.annotations import Platform, skip_platform
from .graphics_common import GraphicsIndexedGenericTestCase, get_feedback, GL_TRIANGLES


@skip_platform(Platform.OSX)  # TODO: Check whether OpenGL < 3.0 or compatibility profile is enabled
class RetainedDrawingIndexedDataTestCase(GraphicsIndexedGenericTestCase, unittest.TestCase):
    def get_feedback(self, data):
        vertex_list = pyglet.graphics.vertex_list_indexed(self.n_vertices, self.index_data, *data)
        return get_feedback(lambda: vertex_list.draw(GL_TRIANGLES))

