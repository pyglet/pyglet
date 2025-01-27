from __future__ import annotations

import ctypes
import sys
from typing import Sequence, TYPE_CHECKING

import pyglet
from pyglet.graphics.api.gl.global_opengl import OpenGLBackend
from pyglet.graphics.api.base import WindowTransformations
from pyglet.graphics.api.gl.gl_compat import glMatrixMode, GL_PROJECTION, glLoadMatrixf, GL_MODELVIEW, glViewport

from pyglet.math import Mat4

if TYPE_CHECKING:
    from pyglet.window import Window

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run


class OpenGL2_Matrices(WindowTransformations):
    def __init__(self, window: Window, backend: OpenGLBackend):
        self._viewport = (0, 0, *window.get_framebuffer_size())

        width, height = window.get_size()
        super().__init__(window, Mat4.orthogonal_projection(0, width, 0, height, -255, 255), Mat4(), Mat4())

        self.projection = self._projection
        self.view = self._view

    @staticmethod
    def _get_mat_float_array(matrix: Mat4):
        return (ctypes.c_float * 16)(*matrix)

    @property
    def projection(self) -> Mat4:
        return self._projection

    @projection.setter
    def projection(self, projection: Mat4):
        self._projection = projection
        glMatrixMode(GL_PROJECTION)
        glLoadMatrixf(self._get_mat_float_array(self._projection))

    @property
    def view(self) -> Mat4:
        return self._view

    @view.setter
    def view(self, view: Mat4):
        self._view = view
        glMatrixMode(GL_MODELVIEW)
        glLoadMatrixf(self._get_mat_float_array(self._view))

    @property
    def model(self) -> Mat4:
        return self._model

    @model.setter
    def model(self, model: Mat4):
        self._model = model

class OpenGL2Backend(OpenGLBackend):

    def get_default_configs(self) -> Sequence[pyglet.graphics.api.gl.OpenGLConfig]:
        """A sequence of configs to use if the user does not specify any.

        These will be used during Window creation.
        """
        return [
            pyglet.graphics.api.gl.OpenGLConfig(self, double_buffer=True, depth_size=24, major_version=2, minor_version=0),
            pyglet.graphics.api.gl.OpenGLConfig(self, double_buffer=True, depth_size=16, major_version=2, minor_version=0),
        ]

    def initialize_matrices(self, window):
        return OpenGL2_Matrices(window, self)
