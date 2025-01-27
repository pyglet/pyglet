from __future__ import annotations

import abc
import threading
import weakref
from enum import Enum
from typing import TYPE_CHECKING, Callable

from pyglet.graphics.api import gl
from pyglet.graphics.api.base import WindowGraphicsContext, GraphicsConfig, VerifiedGraphicsConfig
from pyglet.graphics.api.gl import gl_info, glClearColor

if TYPE_CHECKING:
    from pyglet.window import Window
    from _ctypes import Array
    from pyglet.graphics.api.gl import OpenGLBackend
    from pyglet.graphics.api.gl import GLInfo


class OpenGLAPI(Enum):
    """The OpenGL API backend to use."""
    OPENGL = 1
    OPENGL_ES = 2


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

    @property
    def backend(self) -> OpenGLBackend:
        """The backend object this config belongs to."""
        return self._backend  # type: ignore

    # def create_context(self, window: Window, share: Context | None) -> Context:
    #     """Create a GL context that satisifies this configuration.
    #
    #     Args:
    #         share:
    #             If not ``None``, a context with which to share objects with.
    #     """
    #     if not self.finalized_config:
    #         msg = "This config has not finalized the available attributes."
    #         raise gl.ConfigException(msg)

    #def __repr__(self) -> str:
    #    return f"{self.__class__.__name__}({self.get_gl_attributes()})"


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

    @abc.abstractmethod
    def create_context(self, opengl_backend: OpenGLBackend, share: OpenGLWindowContext) -> OpenGLWindowContext:
        """Create a GL context that satisfies this configuration.

        Args:
            share:
                If not ``None``, a Context with which to share objects with.
        """


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
    #: gl_info.GLInfo instance, filled in on first set_current
    _info: GLInfo | None = None

    #: A container which is shared between all contexts that share GL objects.
    object_space: ObjectSpace
    config: OpenGLWindowConfig
    context_share: OpenGLWindowContext | None

    def __init__(self, global_ctx: OpenGLBackend, window: Window, config: OpenGLWindowConfig, context_share: OpenGLWindowContext | None = None) -> None:
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

        self.doomed_vaos = []
        self.doomed_framebuffers = []

        if context_share:
            self.object_space = context_share.object_space
        else:
            self.object_space = ObjectSpace()

        self.cached_programs = weakref.WeakValueDictionary()

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
        glClearColor(r, g, b, a)

    def clear(self) -> None:
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    def attach(self, window: Window) -> None:
        # if not self.config.compatible(canvas):
        #     msg = f'Cannot attach {canvas} to {self}'
        #     raise RuntimeError(msg)
        self.window = window

    def before_draw(self) -> None:
        self.set_current()

    def set_current(self) -> None:
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

    # For the static functions below:
    # The garbage collector introduces a race condition.
    # The provided list might be appended to (and only appended to) while this
    # method runs, as it's a `doomed_*` list either on the context or its bject
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

        The context will not be useable after being destroyed.  Each platform
        has its own convention for releasing the context and the buffer(s)
        that depend on it in the correct order; this should never be called
        by an application.
        """
        self.detach()

        if self.global_ctx.current_context is self:
            self.global_ctx.current_context = None
            #gl_info.remove_active_context()

            # Switch back to shadow context.
            if self.global_ctx._shadow_window is not None:  # noqa: SLF001
                self.global_ctx._shadow_window.switch_to()  # noqa: SLF001

    def _safe_to_operate_on_object_space(self) -> bool:
        """Check if it's safe to interact with this context's object space.

        This is considered to be the case if the currently active context's
        object space is the same as this context's object space and this
        method is called from the main thread.
        """
        return (self.object_space is self.global_ctx.current_context.object_space and
                threading.current_thread() is threading.main_thread())

    def _safe_to_operate_on(self) -> bool:
        """Check whether it is safe to interact with this context.

        This is considered to be the case if it's the current context and this
        method is called from the main thread.
        """
        return self.global_ctx.current_context is self and threading.current_thread() is threading.main_thread()

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


class ContextException(Exception):
    pass


class ConfigException(Exception):
    pass


