from __future__ import annotations

import abc
import threading
import weakref
from enum import Enum
from typing import TYPE_CHECKING, Callable

import pyglet
from pyglet import gl
from pyglet.gl import gl_info

if TYPE_CHECKING:
    from _ctypes import Array
    from pyglet.display.base import Canvas
    from pyglet.gl.gl_info import GLInfo
    from pyglet.graphics.shader import ShaderProgram


class OpenGLAPI(Enum):
    """The OpenGL API backend to use."""
    OPENGL = 1
    OPENGL_ES = 2


class Config:
    """Graphics configuration.

    A Config stores the preferences for OpenGL attributes such as the
    number of auxiliary buffers, size of the colour and depth buffers,
    double buffering, stencilling, multi- and super-sampling, and so on.

    Different platforms support a different set of attributes, so these
    are set with a string key and a value which is integer or boolean.
    """

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

    _attribute_names = (
        'double_buffer',
        'stereo',
        'buffer_size',
        'aux_buffers',
        'sample_buffers',
        'samples',
        'red_size',
        'green_size',
        'blue_size',
        'alpha_size',
        'depth_size',
        'stencil_size',
        'accum_red_size',
        'accum_green_size',
        'accum_blue_size',
        'accum_alpha_size',
        'major_version',
        'minor_version',
        'forward_compatible',
        'opengl_api',
        'debug',
        'transparent_framebuffer',
    )

    #: The OpenGL major version.
    major_version: int
    #: The OpenGL minor version.
    minor_version: int
    #: Whether to use forward compatibility mode.
    forward_compatible: bool
    #: The OpenGL API, such as "gl" or "gles".
    opengl_api: str
    #: Debug mode.
    debug: bool
    #: If the framebuffer should be transparent.
    transparent_framebuffer: bool

    def __init__(self, **kwargs: float) -> None:
        """Create a template config with the given attributes.

        Specify attributes as keyword arguments, for example::

            template = Config(double_buffer=True)

        """
        for name in self._attribute_names:
            if name in kwargs:
                setattr(self, name, kwargs[name])
            else:
                setattr(self, name, None)

        self.opengl_api = self.opengl_api or "gl"

    def get_gl_attributes(self) -> list[tuple[str, bool | int | str]]:
        """Return a list of attributes set on this config.

        The attributes are returned as a list of tuples, containing
        the name and values. Any unset attributes will have a value
        of ``None``.
        """
        return [(name, getattr(self, name)) for name in self._attribute_names]

    @abc.abstractmethod
    def match(self, canvas: Canvas) -> list[DisplayConfig]:
        """Return a list of matching complete configs for the given canvas."""

    def create_context(self, share: Context | None) -> Context:  # noqa: ARG002
        """Create a GL context that satisfies this configuration.

        Args:
            share:
                If not ``None``, a context with which to share objects with.

        :deprecated: Use `DisplayConfig.create_context`.
        """
        msg = (
            'This config cannot be used to create contexts. '
            'Use Config.match to created a DisplayConfig'
        )
        raise gl.ConfigException(msg)

    def is_complete(self) -> bool:
        """Determine if this config is complete and able to create a context.

        Configs created directly are not complete, they can only serve
        as templates for retrieving a supported config from the system.
        For example, `pyglet.window.Screen.get_matching_configs` returns
        complete configs.

        :deprecated: Use ``isinstance(config, DisplayConfig)``.
        """
        return isinstance(self, DisplayConfig)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.get_gl_attributes()})"


class DisplayConfig(Config, abc.ABC):
    """An OpenGL configuration for a particular display.

    Use ``Config.match`` to obtain an instance of this class.

    .. versionadded:: 1.2
    """
    canvas: Canvas

    def __init__(self, canvas: Canvas, base_config: Config) -> None:
        #: The canvas this config is valid on.
        self.canvas: Canvas = canvas

        self.major_version = base_config.major_version
        self.minor_version = base_config.minor_version
        self.forward_compatible = base_config.forward_compatible
        self.opengl_api = base_config.opengl_api or self.opengl_api
        self.debug = base_config.debug
        self.transparent_framebuffer = base_config.transparent_framebuffer

    @abc.abstractmethod
    def compatible(self, canvas: Canvas) -> bool:
        """Determine compatibility with the canvas."""

    @abc.abstractmethod
    def create_context(self, share: Context) -> Context:
        """Create a GL context that satisfies this configuration.

        Args:
            share:
                If not ``None``, a Context with which to share objects with.
        """

    def is_complete(self) -> bool:
        return True


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


class Context:
    """A base OpenGL context for drawing.

    Use ``DisplayConfig.create_context`` to create a context.
    """
    #: gl_info.GLInfo instance, filled in on first set_current
    _info: GLInfo | None = None

    #: A container which is shared between all contexts that share GL objects.
    object_space: ObjectSpace
    config: DisplayConfig
    context_share: Context | None

    def __init__(self, config: DisplayConfig, context_share: Context | None = None) -> None:
        """Initialize a context.

        This should only be created through the ``DisplayConfig.create_context`` method.

        Args:
            config:
                An operating system specific config.
            context_share:
                A context to share objects with. Use ``None`` to disable sharing.
        """
        self.config = config
        self.context_share = context_share
        self.canvas = None

        self.doomed_vaos = []
        self.doomed_framebuffers = []

        if context_share:
            self.object_space = context_share.object_space
        else:
            self.object_space = ObjectSpace()

        self._cached_programs = weakref.WeakValueDictionary()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={id(self)}, share={self.context_share})"

    def __enter__(self) -> None:
        self.set_current()

    def __exit__(self, *_args) -> None:  # noqa: ANN002
        return

    def attach(self, canvas: Canvas) -> None:
        if self.canvas is not None:
            self.detach()
        if not self.config.compatible(canvas):
            msg = f'Cannot attach {canvas} to {self}'
            raise RuntimeError(msg)
        self.canvas = canvas

    def detach(self) -> None:
        self.canvas = None

    def set_current(self) -> None:
        """Make this the active Context.

        Setting the Context current will also delete any OpenGL
        objects that have been queued for deletion. IE: any objects
        that were created in this Context, but have been called for
        deletion while another Context was active.
        """
        if not self.canvas:
            msg = 'Canvas has not been attached'
            raise RuntimeError(msg)

        # Not per-thread
        gl.current_context = self

        # Set active context.
        gl_info.set_active_context()

        if not self._info:
            self._info = gl_info.GLInfo()
            self._info.set_active_context()

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

    # For the static functions below:
    # The garbage collector introduces a race condition.
    # The provided list might be appended to (and only appended to) while this
    # method runs, as it's a `doomed_*` list either on the context or its object
    # space. If `count` wasn't stored in a local, this method might leak objects.
    @staticmethod
    def _delete_objects(list_: list, deletion_func: Callable[[int, Array[gl.GLuint]], None]) -> None:
        """Release all OpenGL objects in the given list.

        Uses the supplied deletion function with the signature ``(GLuint count, GLuint *names)``.
        """
        count = len(list_)
        to_delete = list_[:count]
        del list_[:count]

        deletion_func(count, (gl.GLuint * count)(*to_delete))

    @staticmethod
    def _delete_objects_one_by_one(list_: list, deletion_func: Callable[[gl.GLuint], None]) -> None:
        """Release all OpenGL objects in the given list.

        Similar to ``_delete_objects``, but assumes the deletion function's signature to be ``(GLuint name)``.

        The function is called for each object.
        """
        count = len(list_)
        to_delete = list_[:count]
        del list_[:count]

        for name in to_delete:
            deletion_func(gl.GLuint(name))

    def destroy(self) -> None:
        """Release the Context.

        The context will not be usable after being destroyed.  Each platform
        has its own convention for releasing the context and the buffer(s)
        that depend on it in the correct order; this should never be called
        by an application.
        """
        self.detach()

        if gl.current_context is self:
            gl.current_context = None
            gl_info.remove_active_context()

            # Switch back to shadow context.
            if gl._shadow_window is not None:  # noqa: SLF001
                gl._shadow_window.switch_to()  # noqa: SLF001

    def _safe_to_operate_on_object_space(self) -> bool:
        """Check if it's safe to interact with this context's object space.

        This is considered to be the case if the currently active context's
        object space is the same as this context's object space and this
        method is called from the main thread.
        """
        return (self.object_space is gl.current_context.object_space and
                threading.current_thread() is threading.main_thread())

    def _safe_to_operate_on(self) -> bool:
        """Check whether it is safe to interact with this context.

        This is considered to be the case if it's the current context and this
        method is called from the main thread.
        """
        return gl.current_context is self and threading.current_thread() is threading.main_thread()

    def create_program(self, *sources: tuple[str, str]) -> ShaderProgram:
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
        if program := self._cached_programs.get(str(sources)):
            return program

        shaders = (pyglet.graphics.shader.Shader(src, srctype) for (src, srctype) in sources)
        program = pyglet.graphics.shader.ShaderProgram(*shaders)
        self._cached_programs[str(sources)] = program

        return program

    def delete_texture(self, texture_id: int) -> None:
        """Safely delete a Texture belonging to this context's object space.

        This method will delete the texture immediately via
        ``glDeleteTextures`` if the current context's object space is the same
        as this context's object space, and it is called from the main thread.

        Otherwise, the texture will only be marked for deletion, postponing
        it until any context with the same object space becomes active again.

        This makes it safe to call from anywhere, including other threads.
        """
        if self._safe_to_operate_on_object_space():
            gl.glDeleteTextures(1, gl.GLuint(texture_id))
        else:
            self.object_space.doomed_textures.append(texture_id)

    def delete_buffer(self, buffer_id: int) -> None:
        """Safely delete a Buffer belonging to this context's object space.

        This method behaves similarly to ``delete_texture``, though for
        ``glDeleteBuffers`` instead of ``glDeleteTextures``.
        """
        if self._safe_to_operate_on_object_space():
            gl.glDeleteBuffers(1, gl.GLuint(buffer_id))
        else:
            self.object_space.doomed_buffers.append(buffer_id)

    def delete_shader_program(self, program_id: int) -> None:
        """Safely delete a ShaderProgram belonging to this context's object space.

        This method behaves similarly to ``delete_texture``, though for
        ``glDeleteProgram`` instead of ``glDeleteTextures``.
        """
        if self._safe_to_operate_on_object_space():
            gl.glDeleteProgram(gl.GLuint(program_id))
        else:
            self.object_space.doomed_shader_programs.append(program_id)

    def delete_shader(self, shader_id: int) -> None:
        """Safely delete a Shader belonging to this context's object space.

        This method behaves similarly to ``delete_texture``, though for
        ``glDeleteShader`` instead of ``glDeleteTextures``.
        """
        if self._safe_to_operate_on_object_space():
            gl.glDeleteShader(gl.GLuint(shader_id))
        else:
            self.object_space.doomed_shaders.append(shader_id)

    def delete_renderbuffer(self, rbo_id: int) -> None:
        """Safely delete a Renderbuffer belonging to this context's object space.

        This method behaves similarly to ``delete_texture``, though for
        ``glDeleteRenderbuffers`` instead of ``glDeleteTextures``.
        """
        if self._safe_to_operate_on_object_space():
            gl.glDeleteRenderbuffers(1, gl.GLuint(rbo_id))
        else:
            self.object_space.doomed_renderbuffers.append(rbo_id)

    def delete_vao(self, vao_id: int) -> None:
        """Safely delete a Vertex Array Object belonging to this context.

        If this context is not the current context or this method is not
        called from the main thread, its deletion will be postponed until
        this context is next made active again.

        Otherwise, this method will immediately delete the VAO via
        ``glDeleteVertexArrays``.
        """
        if self._safe_to_operate_on():
            gl.glDeleteVertexArrays(1, gl.GLuint(vao_id))
        else:
            self.doomed_vaos.append(vao_id)

    def delete_framebuffer(self, fbo_id: int) -> None:
        """Safely delete a Framebuffer Object belonging to this context.

        This method behaves similarly to ``delete_vao``, though for
        ``glDeleteFramebuffers`` instead of ``glDeleteVertexArrays``.
        """
        if self._safe_to_operate_on():
            gl.glDeleteFramebuffers(1, gl.GLuint(fbo_id))
        else:
            self.doomed_framebuffers.append(fbo_id)

    def get_info(self) -> GLInfo:
        """Get the :py:class:`~GLInfo` instance for this context."""
        return self._info
