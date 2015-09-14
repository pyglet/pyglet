#!/usr/bin/env python
"""Tests immediate drawing using indexed data.
"""
from __future__ import absolute_import
import unittest

import pyglet

from tests.annotations import Platform, skip_platform
from .graphics_common import GraphicsIndexedGenericTestCase, get_feedback, GL_TRIANGLES


@skip_platform(Platform.OSX)  # TODO: Check whether OpenGL < 3.0 or compatibility profile is enabled
class ImmediateDrawingIndexedDataTestCase(GraphicsIndexedGenericTestCase, unittest.TestCase):
    def get_feedback(self, data):
        return get_feedback(lambda: pyglet.graphics.draw_indexed(self.n_vertices,
                                                                 GL_TRIANGLES,
                                                                 self.index_data,
                                                                 *data))

