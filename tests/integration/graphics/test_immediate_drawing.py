#!/usr/bin/env python
"""Tests immediate drawing.
"""
from __future__ import absolute_import
import unittest

import pyglet

from .graphics_common import GraphicsGenericTestCase, get_feedback, GL_TRIANGLES


class ImmediateDrawingTestCase(GraphicsGenericTestCase, unittest.TestCase):
    def get_feedback(self, data):
        return get_feedback(lambda: pyglet.graphics.draw(self.n_vertices, GL_TRIANGLES, *data))

