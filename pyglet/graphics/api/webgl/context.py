from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, Any, Callable

import js
from pyodide.ffi import create_proxy

from pyglet.graphics.api.base import SurfaceContext
from pyglet.graphics.api.webgl import gl
from pyglet.graphics.api.webgl.gl import GL_COLOR_BUFFER_BIT
from pyglet.graphics.api.webgl.gl_info import GLInfo
from pyglet.graphics.api.webgl.shader import GLDataType

if TYPE_CHECKING:
    from pyglet.graphics.api import WebGLBackend
    from pyglet.graphics.api.webgl.config import OpenGLWindowConfig
    from pyglet.graphics.api.webgl.webgl_js import WebGL2RenderingContext
    from pyglet.window import Window
    from pyglet.window.emscripten import EmscriptenWindow


class ObjectSpace:
    """A container to store shared objects that are to be removed."""

    def __init__(self) -> None:
        """Initialize the context object space."""
        # Objects scheduled for deletion the next time this object space is active.
        self.doomed_textures = []
        self.doomed_buffers = []
        self.doomed_shader_programs = []
        self.doomed_shaders = []
        self.doomed_renderbuffers = []


class OpenGLSurfaceContext(SurfaceContext):
    """A base OpenGL context for drawing.

    Use ``DisplayConfig.create_context`` to create a context.
    """

    gl: WebGL2RenderingContext
    config: OpenGLWindowConfig
    context_share: OpenGLSurfaceContext | None

    def __init__(
        self,
        global_ctx: WebGLBackend,
        window: EmscriptenWindow,
        config: OpenGLWindowConfig,  # noqa: D417
        context_share: OpenGLSurfaceContext | None = None,
    ) -> None:
        """Initialize a context.

        This should only be created through the ``DisplayConfig.create_context`` method.

        Args:
            config:
                An operating system specific config.
            context_share:
                A context to share objects with. Use ``None`` to disable sharing.
        """
        super().__init__(global_ctx, window, config)
        self.global_ctx = global_ctx
        self.window = window
        self.config = config
        self.context_share = context_share
        self.is_current = False

        # The GL Context.
        self.gl = self.window.canvas.getContext("webgl2")

        self._info = GLInfo()
        self._info.query(self.gl)
        self.object_space = ObjectSpace()

        self._draw_proxy = create_proxy(self.window.draw)

        self._clear_color = (0.0, 0.0, 0.0, 1.0)

        self.doomed_vaos = []
        self.doomed_framebuffers = []

        self.cached_programs = weakref.WeakValueDictionary()
        self._create_uniform_dicts()

    def get_info(self) -> GLInfo:
        """Get the :py:class:`~GLInfo` instance for this context."""
        return self._info

    def resized(self, width, height): ...

    def detach(self):
        self.context = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={id(self)}, share={self.context_share})"

    def __enter__(self) -> None:
        self.set_current()

    def __exit__(self, *_args) -> None:  # noqa: ANN002
        return

    def set_clear_color(self, r: float, g: float, b: float, a: float) -> None:
        self._clear_color = (r, g, b, a)

    def clear(self) -> None:
        self.gl.clear(GL_COLOR_BUFFER_BIT)

    def flip(self):
        pass

    def destroy(self) -> None:
        """Release the Context.

        The context will not be useable after being destroyed.  Each platform
        has its own convention for releasing the context and the buffer(s)
        that depend on it in the correct order; this should never be called
        by an application.
        """
        # self.detach()
        #
        if self.core.current_context is self:
            self.core.current_context = None
        #     #gl_info.remove_active_context()

    def attach(self, window: Window) -> None:
        # if not self.config.compatible(canvas):
        #     msg = f'Cannot attach {canvas} to {self}'
        #     raise RuntimeError(msg)
        self.window = window

    def before_draw(self) -> None:
        self.gl.clearColor(*self._clear_color)
        self.gl.clear(GL_COLOR_BUFFER_BIT)

    def set_current(self) -> None:
        return
        """Make this the active Context.

        Setting the Context current will also delete any OpenGL
        objects that have been queued for deletion. IE: any objects
        that were created in this Context, but have been called for
        deletion while another Context was active.
        """
        assert self.window is not None, "Window has not been attached."

        # Not per-thread
        self.global_ctx.current_context = self
        gl.current_context = self

        # Set active context.
        # gl_info.set_active_context()

        if not self._info.was_queried:
            self._info.query()

        if self.object_space.doomed_textures:
            self._delete_objects(self.object_space.doomed_textures, gl.glDeleteTextures)
        if self.object_space.doomed_buffers:
            self._delete_objects(self.object_space.doomed_buffers, gl.glDeleteBuffers)
        if self.object_space.doomed_shader_programs:
            self._delete_objects_one_by_one(self.object_space.doomed_shader_programs, gl.glDeleteProgram)
        if self.object_space.doomed_shaders:
            self._delete_objects_one_by_one(self.object_space.doomed_shaders, gl.glDeleteShader)
        if self.object_space.doomed_renderbuffers:
            self._delete_objects(self.object_space.doomed_renderbuffers, gl.glDeleteRenderbuffers)

        if self.doomed_vaos:
            self._delete_objects(self.doomed_vaos, gl.glDeleteVertexArrays)
        if self.doomed_framebuffers:
            self._delete_objects(self.doomed_framebuffers, gl.glDeleteFramebuffers)

    def _create_uniform_dicts(self) -> None:
        self._uniform_setters: dict[int, tuple[GLDataType, Callable, int]] = {
            # uniform: gl_type, setter, length
            gl.GL_BOOL: (gl.GLint, self.gl.uniform1i, 1),
            gl.GL_BOOL_VEC2: (gl.GLint, self.gl.uniform2iv, 2),
            gl.GL_BOOL_VEC3: (gl.GLint, self.gl.uniform3iv, 3),
            gl.GL_BOOL_VEC4: (gl.GLint, self.gl.uniform4iv, 4),
            gl.GL_INT: (gl.GLint, self.gl.uniform1i, 1),
            gl.GL_INT_VEC2: (gl.GLint, self.gl.uniform2iv, 2),
            gl.GL_INT_VEC3: (gl.GLint, self.gl.uniform3iv, 3),
            gl.GL_INT_VEC4: (gl.GLint, self.gl.uniform4iv, 4),
            gl.GL_FLOAT: (gl.GLfloat, self.gl.uniform1f, 1),
            gl.GL_FLOAT_VEC2: (gl.GLfloat, self.gl.uniform2fv, 2),
            gl.GL_FLOAT_VEC3: (gl.GLfloat, self.gl.uniform3fv, 3),
            gl.GL_FLOAT_VEC4: (gl.GLfloat, self.gl.uniform4fv, 4),
            # 1D Samplers
            gl.GL_SAMPLER_1D: (gl.GLint, self.gl.uniform1i, 1),
            gl.GL_SAMPLER_1D_ARRAY: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_INT_SAMPLER_1D: (gl.GLint, self.gl.uniform1i, 1),
            gl.GL_INT_SAMPLER_1D_ARRAY: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_1D: (gl.GLint, self.gl.uniform1i, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_1D_ARRAY: (gl.GLint, self.gl.uniform1iv, 1),
            # 2D Samplers
            gl.GL_SAMPLER_2D: (gl.GLint, self.gl.uniform1i, 1),
            gl.GL_SAMPLER_2D_ARRAY: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_INT_SAMPLER_2D: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_INT_SAMPLER_2D_ARRAY: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_2D: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_2D_ARRAY: (gl.GLint, self.gl.uniform1iv, 1),
            # Multisample
            gl.GL_SAMPLER_2D_MULTISAMPLE: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_INT_SAMPLER_2D_MULTISAMPLE: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE: (gl.GLint, self.gl.uniform1iv, 1),
            # Cube Samplers
            gl.GL_SAMPLER_CUBE: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_INT_SAMPLER_CUBE: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_CUBE: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_SAMPLER_CUBE_MAP_ARRAY: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_INT_SAMPLER_CUBE_MAP_ARRAY: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_CUBE_MAP_ARRAY: (gl.GLint, self.gl.uniform1iv, 1),
            # 3D Samplers
            gl.GL_SAMPLER_3D: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_INT_SAMPLER_3D: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_3D: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_FLOAT_MAT2: (gl.GLfloat, self.gl.uniformMatrix2fv, 4),
            gl.GL_FLOAT_MAT3: (gl.GLfloat, self.gl.uniformMatrix3fv, 6),
            gl.GL_FLOAT_MAT4: (gl.GLfloat, self.gl.uniformMatrix4fv, 16),
            # Images
            gl.GL_IMAGE_1D: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_IMAGE_2D: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_IMAGE_2D_RECT: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_IMAGE_3D: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_IMAGE_1D_ARRAY: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_IMAGE_2D_ARRAY: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_IMAGE_2D_MULTISAMPLE: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_IMAGE_2D_MULTISAMPLE_ARRAY: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_IMAGE_BUFFER: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_IMAGE_CUBE: (gl.GLint, self.gl.uniform1iv, 1),
            gl.GL_IMAGE_CUBE_MAP_ARRAY: (gl.GLint, self.gl.uniform1iv, 1),
        }
