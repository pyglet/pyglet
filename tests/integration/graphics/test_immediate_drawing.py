#!/usr/bin/env python
"""Tests immediate drawing.
"""
from __future__ import absolute_import
import unittest

import pyglet

from tests.annotations import Platform, skip_platform
from .graphics_common import GraphicsGenericTestCase, get_feedback, GL_TRIANGLES


@skip_platform(Platform.OSX)  # TODO: Check whether OpenGL < 3.0 or compatibility profile is enabled
class ImmediateDrawingTestCase(GraphicsGenericTestCase, unittest.TestCase):
    def get_feedback(self, data):
        return get_feedback(lambda: pyglet.graphics.draw(self.n_vertices, GL_TRIANGLES, *data))

