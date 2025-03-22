from __future__ import annotations

import ctypes
import sys
import js
from pyodide.ffi import create_proxy
import warnings
import weakref
from typing import Sequence, TYPE_CHECKING

import pyglet
from pyglet.graphics.api.webgl import gl_info
from pyglet.graphics.api.webgl.shader import Shader, ShaderProgram
from pyglet.graphics.api.base import BackendGlobalObject, GraphicsConfig, VerifiedGraphicsConfig, WindowGraphicsContext, \
    UBOMatrixTransformations
from pyglet.graphics.api.webgl.gl import glViewport
from pyglet.math import Mat4

if TYPE_CHECKING:
    from pyglet.graphics.shader import ShaderType
    from pyglet.window import Window

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run



class OpenGL3_Matrices(UBOMatrixTransformations):
    # Create a default ShaderProgram, so the Window instance can
    # update the `WindowBlock` UBO shared by all default shaders.
    _default_vertex_source = """#version 300 es
         in vec4 position;

         uniform WindowBlock
         {
             mat4 projection;
             mat4 view;
         } window;

         void main()
         {
             gl_Position = window.projection * window.view * position;
         }
     """
    _default_fragment_source = """#version 300 es
         out vec4 color;

         void main()
         {
             color = vec4(1.0, 0.0, 0.0, 1.0);
         }
     """

    def __init__(self, window: Window, backend: WebGLBackend):

        self._default_program = backend.create_shader_program(
            backend.create_shader(self._default_vertex_source, 'vertex'),
            backend.create_shader(self._default_fragment_source, 'fragment'))

        window_block = self._default_program.uniform_blocks['WindowBlock']
        self.ubo = window_block.create_ubo()
        window_block.bind(self.ubo)

        self._viewport = (0, 0, *window.get_framebuffer_size())

        width, height = window.get_size()

        super().__init__(window, Mat4.orthogonal_projection(0, width, 0, height, -255, 255), Mat4(), Mat4())

        with self.ubo as window_block:
            window_block.view[:] = self._view
            window_block.projection[:] = self._projection

    @property
    def projection(self) -> Mat4:
        return self._projection

    @projection.setter
    def projection(self, projection: Mat4):
        with self.ubo as window_block:
            window_block.projection[:] = projection

        self._projection = projection

    @property
    def view(self) -> Mat4:
        return self._view

    @view.setter
    def view(self, view: Mat4):
        with self.ubo as window_block:
            window_block.view[:] = view

        self._view = view

    @property
    def model(self) -> Mat4:
        return self._model

    @model.setter
    def model(self, model: Mat4):
        with self.ubo as window_block:
            window_block.model[:] = model

        self._model = model

class OpenGLWindowConfig(VerifiedGraphicsConfig):
    """An OpenGL configuration for a particular display.

    Use ``Config.match`` to obtain an instance of this class.

    .. versionadded:: 1.2
    """

    def __init__(self, window: Window, base_config: OpenGLConfig) -> None:
        super().__init__(window, base_config)
        self.major_version = base_config.major_version
        self.minor_version = base_config.minor_version
        self.forward_compatible = base_config.forward_compatible
        self.opengl_api = base_config.opengl_api or base_config.opengl_api
        self.debug = base_config.debug

    def create_context(self, opengl_backend: WebGLBackend, share: OpenGLWindowContext) -> OpenGLWindowContext:
        """Create a GL context that satisfies this configuration.

        Args:
            share:
                If not ``None``, a Context with which to share objects with.
        """
        return OpenGLWindowContext(opengl_backend, self._window, self._config, None)

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

class OpenGLWindowContext(WindowGraphicsContext):
    """A base OpenGL context for drawing.

    Use ``DisplayConfig.create_context`` to create a context.
    """
    config: OpenGLWindowConfig
    context_share: OpenGLWindowContext | None

    def __init__(self, global_ctx: WebGLBackend, window: Window, config: OpenGLWindowConfig, context_share: OpenGLWindowContext | None = None) -> None:
        """Initialize a context.

        This should only be created through the ``DisplayConfig.create_context`` method.

        Args:
            config:
                An operating system specific config.
            context_share:
                A context to share objects with. Use ``None`` to disable sharing.
        """
        self.global_ctx = global_ctx
        self.window = window
        self.config = config
        self.context_share = context_share
        self.is_current = False
        self._info = gl_info.GLInfo()
        self.object_space = ObjectSpace()

        self.context = self.window.canvas.getContext("webgl2")

        from pyglet.graphics.api.webgl import gl

        self._draw_proxy = create_proxy(self.window.draw)

        self._clear_color = (0.0, 0.0, 0.0, 1.0)

        self.doomed_vaos = []
        self.doomed_framebuffers = []

        self.cached_programs = weakref.WeakValueDictionary()

    def get_info(self) -> gl_info.GLInfo:
        """Get the :py:class:`~GLInfo` instance for this context."""
        return self._info

    def start_render(self):
        js.requestAnimationFrame(self._draw_proxy)
        print("START RENDER")

    def resized(self, width, height):
        ...

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
        self.context.clear(self.context.COLOR_BUFFER_BIT)

    def flip(self):
        js.requestAnimationFrame(self._draw_proxy)

    def attach(self, window: Window) -> None:
        # if not self.config.compatible(canvas):
        #     msg = f'Cannot attach {canvas} to {self}'
        #     raise RuntimeError(msg)
        self.window = window

    def before_draw(self) -> None:
        self.context.clearColor(*self._clear_color)
        self.context.clear(self.context.COLOR_BUFFER_BIT)

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
        #gl_info.set_active_context()

        if not self._info.was_queried:
            self._info.query()

        if self.object_space.doomed_textures:
            self._delete_objects(self.object_space.doomed_textures, gl.glDeleteTextures)
        if self.object_space.doomed_buffers:
            self._delete_objects(self.object_space.doomed_buffers, gl.glDeleteBuffers)
        if self.object_space.doomed_shader_programs:
            self._delete_objects_one_by_one(self.object_space.doomed_shader_programs,
                                            gl.glDeleteProgram)
        if self.object_space.doomed_shaders:
            self._delete_objects_one_by_one(self.object_space.doomed_shaders, gl.glDeleteShader)
        if self.object_space.doomed_renderbuffers:
            self._delete_objects(self.object_space.doomed_renderbuffers, gl.glDeleteRenderbuffers)

        if self.doomed_vaos:
            self._delete_objects(self.doomed_vaos, gl.glDeleteVertexArrays)
        if self.doomed_framebuffers:
            self._delete_objects(self.doomed_framebuffers, gl.glDeleteFramebuffers)

class OpenGLConfig(GraphicsConfig):
    """An OpenGL Graphics configuration."""
    #: Specify the presence of a back-buffer for every color buffer.
    double_buffer: bool
    #: Specify the presence of separate left and right buffer sets.
    stereo: bool
    #: Total bits per sample per color buffer.
    buffer_size: int
    #: The number of auxiliary color buffers.
    aux_buffers: int
    #: The number of multisample buffers.
    sample_buffers: int
    #: The number of samples per pixel, or 0 if there are no multisample buffers.
    samples: int
    #: Bits per sample per buffer devoted to the red component.
    red_size: int
    #: Bits per sample per buffer devoted to the green component.
    green_size: int
    #: Bits per sample per buffer devoted to the blue component.
    blue_size: int
    #: Bits per sample per buffer devoted to the alpha component.
    alpha_size: int
    #: Bits per sample in the depth buffer.
    depth_size: int
    #: Bits per sample in the stencil buffer.
    stencil_size: int
    #: Bits per pixel devoted to the red component in the accumulation buffer.
    accum_red_size: int
    #: Bits per pixel devoted to the green component in the accumulation buffer.
    accum_green_size: int
    #: Bits per pixel devoted to the blue component in the accumulation buffer.
    accum_blue_size: int
    #: Bits per pixel devoted to the alpha component in the accumulation buffer.
    accum_alpha_size: int
    #: The OpenGL major version.
    major_version: int
    #: The OpenGL minor version.
    minor_version: int
    #: Whether to use forward compatibility mode.
    forward_compatible: bool
    #: The OpenGL API, such as "gl" or "gles".
    opengl_api: str = "gl"
    #: Debug mode.
    debug: bool

    def match(self, window: Window) -> OpenGLWindowConfig:
        return OpenGLWindowConfig(window, self)

    @property
    def finalized_config(self) -> OpenGLWindowConfig | None:
        return self._finalized_config

    def get_gl_attributes(self) -> list[tuple[str, bool | int | str]]:
        """Return a list of attributes set on this config.

        The attributes are returned as a list of tuples, containing
        the name and values. Any unset attributes will have a value
        of ``None``.
        """
        return [(name, getattr(self, name)) for name in self._attributes]


class WebGLBackend(BackendGlobalObject):
    current_context: OpenGLWindowContext | None
    _have_context: bool = False

    def __init__(self) -> None:
        self.initialized = False
        self.current_context = None
        self._shadow_window = None

        # When the shadow window is created, a context is made. This is used to help the "real" context to utilize
        # its full capabilities; however, the two contexts have no relationship normally. This is used for the purpose
        # of sharing basic information between contexts. However, in usage, the user or internals should use the
        # "real" context's information to prevent any discrepencies.
        #self.gl_info = GLInfo()  # GL Info is a shared info space.
        super().__init__()

    @property
    def object_space(self) -> ObjectSpace:
        assert self.current_context is not None, "Context has not been created."
        return self.current_context.object_space

    def post_init(self) -> None:
        pass

    def create_context(self, config: OpenGLWindowConfig, shared: OpenGLWindowContext | None):
        return config.create_context(self, shared)

    def get_window_backend_context(self, window: Window, config: OpenGLWindowConfig) -> WindowGraphicsContext:
        """We will always only have one context in this Backend."""
        assert self.current_context is None
        context = self.windows[window] = self.create_context(config, self.current_context)
        self.current_context = context
        self._have_context = True
        return context

    def get_default_configs(self) -> Sequence[OpenGLConfig]:
        """A sequence of configs to use if the user does not specify any.

        These will be used during Window creation.
        """
        return [
            OpenGLConfig(double_buffer=True, depth_size=24, major_version=3, minor_version=3),
            OpenGLConfig(double_buffer=True, depth_size=16, major_version=3, minor_version=3),
        ]

    def get_config(self, **kwargs: float | str | None) -> OpenGLConfig:
        return OpenGLConfig(**kwargs)

    def get_info(self):
        return self.current_context.get_info()

    def have_extension(self, extension_name: str) -> bool:
        if not self.current_context:
            warnings.warn('No GL context created yet or current context not set.')
            return False

        return self.current_context.get_info().have_extension(extension_name)

    def have_version(self, major: int, minor: int = 0) -> bool:
        if not self.current_context:
            warnings.warn('No GL context created yet or current context not set.')
            return False

        return self.current_context.get_info().have_version(major, minor)

    def get_cached_shader(self, name: str, *sources: tuple[str, ShaderType]) -> ShaderProgram:
        """Create a ShaderProgram from OpenGL GLSL source.

        This is a convenience method that takes one or more tuples of
        (source_string, shader_type), and returns a
        :py:class:`~pyglet.graphics.shader.ShaderProgram` instance.

        ``source_string`` is OpenGL GLSL source code as a str, and ``shader_type``
        is the OpenGL shader type, such as "vertex" or "fragment". See
        :py:class:`~pyglet.graphics.shader.Shader` for more information.

        .. note:: This method is cached. Given the same shader sources, the
                  same ShaderProgram instance will be returned. For more
                  control over the ShaderProgram lifecycle, it is recommended
                  to manually create Shaders and link ShaderPrograms.

        .. versionadded:: 2.0.10
        """
        assert self.current_context
        assert isinstance(name, str), "First argument must be a string name for the shader."
        if program := self.current_context.cached_programs.get(name):
            return program

        shaders = (Shader(src, srctype) for (src, srctype) in sources)
        program = ShaderProgram(*shaders)
        self.current_context.cached_programs[name] = program
        return program

    def create_shader_program(self, *shaders: Shader) -> ShaderProgram:
        return ShaderProgram(*shaders)

    def create_shader(self, source_string: str, shader_type: ShaderType) -> Shader:
        return Shader(source_string, shader_type)

    def get_default_batch(self) -> pyglet.graphics.Batch:
        assert self.current_context
        if not hasattr(self.current_context, "default_batch"):
            self.current_context.default_batch = pyglet.graphics.Batch()

        return self.current_context.default_batch

    @property
    def have_context(self) -> bool:
        return self._have_context

    def initialize_matrices(self, window):
        return OpenGL3_Matrices(window, self)

    def set_viewport(self, window, x: int, y: int, width: int, height: int) -> None:
        glViewport(x, y, width, height)
