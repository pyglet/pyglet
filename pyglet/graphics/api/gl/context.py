from __future__ import annotations

import threading
import weakref
from typing import Callable, TYPE_CHECKING

from pyglet.graphics.api.gl import gl, gl_info, ObjectSpace
from pyglet.graphics.api.base import SurfaceContext
from pyglet.graphics.api.gl.gl import GLFunctions, GLuint, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT


if TYPE_CHECKING:
    from pyglet.config import SurfaceConfig
    from pyglet.graphics.api.gl.shader import GLDataType, GLFunc
    from ctypes import Array
    from pyglet.window import Window
    from pyglet.graphics.api.gl.xlib.glx_info import GLXInfo
    from pyglet.graphics.api.gl.win32.wgl_info import WGLInfo
    from pyglet.graphics.api.gl.global_opengl import OpenGLBackend
    from pyglet.graphics.api.gl.framebuffer import Framebuffer


class OpenGLSurfaceContext(SurfaceContext, GLFunctions):
    """A base OpenGL context for drawing.

    Use ``DisplayConfig.create_context`` to create a context.
    """
    gles_pixel_fbo: Framebuffer | None
    #: gl_info.GLInfo instance, filled in on first set_current
    _info: gl_info.GLInfo | None = None

    #: A container which is shared between all contexts that share GL objects.
    object_space: ObjectSpace
    config: SurfaceConfig
    context_share: OpenGLSurfaceContext | None

    def __init__(self, core: OpenGLBackend,
                 window: Window,
                 config: SurfaceConfig,
                 platform_info: GLXInfo | WGLInfo | None = None,
                 context_share: OpenGLSurfaceContext | None = None,
                 platform_func_class: type | None = None) -> None:
        """Initialize a context.

        Args:
            config:
                An operating system specific config.
            context_share:
                A context to share objects with. Use ``None`` to disable sharing.
        """
        self._context = None
        self.core = core
        self.window = window
        self.config = config
        #super().__init__(core, window, config)
        self.context_share = context_share
        self.is_current = False
        self._info = gl_info.GLInfo(platform_info)
        self.platform_func_class = platform_func_class
        self.platform_func = None

        self.doomed_vaos = []
        self.doomed_framebuffers = []

        if context_share:
            self.object_space = context_share.object_space
        else:
            self.object_space = ObjectSpace()

        self.cached_programs = weakref.WeakValueDictionary()

        # GLES needs an FBO to read pixel data.
        self.gles_pixel_fbo = None

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
        self.glClearColor(r, g, b, a)

    def clear(self) -> None:
        self.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def attach(self, window: Window) -> None:
        """Attaches a Window and context to the current window.

        The OS specific child classes create contexts or GL related OS resources.

        This mostly exists because of Xlib, as GLXWindow requires XWindow creation before the GLXWindow is created.
        However, the GLX Context needs to be created before the XWindow, due to matching
        assign_config (glx_context is created) -> XWindow creation -> Create GLXWindow
        """
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
        # Not per-thread
        self.core.current_context = self

        if not self._info.was_queried:
            GLFunctions.__init__(self)
            # Move this later to a better platform implementation.
            if not self.platform_func and self.platform_func_class:
                self.platform_func = self.platform_func_class()
            self.uniform_getters, self.uniform_setters = self._get_uniform_func_tables()
            self._info.query(self)
            if self.get_info().get_opengl_api() == "gles":
                from pyglet.graphics.api.gl.framebuffer import Framebuffer
                self.gles_pixel_fbo = Framebuffer(context=self)

        if self.object_space.doomed_textures:
            self._delete_objects(self.object_space.doomed_textures, self.glDeleteTextures)
        if self.object_space.doomed_buffers:
            self._delete_objects(self.object_space.doomed_buffers, self.glDeleteBuffers)
        if self.object_space.doomed_shader_programs:
            self._delete_objects_one_by_one(self.object_space.doomed_shader_programs,
                                            self.glDeleteProgram)
        if self.object_space.doomed_shaders:
            self._delete_objects_one_by_one(self.object_space.doomed_shaders, self.glDeleteShader)
        if self.object_space.doomed_renderbuffers:
            self._delete_objects(self.object_space.doomed_renderbuffers, self.glDeleteRenderbuffers)

        if self.doomed_vaos:
            self._delete_objects(self.doomed_vaos, self.glDeleteVertexArrays)
        if self.doomed_framebuffers:
            self._delete_objects(self.doomed_framebuffers, self.glDeleteFramebuffers)

    # For the static functions below:
    # The garbage collector introduces a race condition.
    # The provided list might be appended to (and only appended to) while this
    # method runs, as it's a `doomed_*` list either on the context or its bject
    # space. If `count` wasn't stored in a local, this method might leak objects.
    @staticmethod
    def _delete_objects(list_: list, deletion_func: Callable[[int, Array[GLuint]], None]) -> None:
        """Release all OpenGL objects in the given list.

        Uses the supplied deletion function with the signature ``(GLuint count, GLuint *names)``.
        """
        count = len(list_)
        to_delete = list_[:count]
        del list_[:count]

        deletion_func(count, (GLuint * count)(*to_delete))

    @staticmethod
    def _delete_objects_one_by_one(list_: list, deletion_func: Callable[[GLuint], None]) -> None:
        """Release all OpenGL objects in the given list.

        Similar to ``_delete_objects``, but assumes the deletion function's signature to be ``(GLuint name)``.

        The function is called for each object.
        """
        count = len(list_)
        to_delete = list_[:count]
        del list_[:count]

        for name in to_delete:
            deletion_func(GLuint(name))

    def destroy(self) -> None:
        """Release the Context.

        The context will not be useable after being destroyed.  Each platform
        has its own convention for releasing the context and the buffer(s)
        that depend on it in the correct order; this should never be called
        by an application.
        """
        self.detach()

        if self.core.current_context is self:
            self.core.current_context = None
            #gl_info.remove_active_context()

    def _safe_to_operate_on_object_space(self) -> bool:
        """Check if it's safe to interact with this context's object space.

        This is considered to be the case if the currently active context's
        object space is the same as this context's object space and this
        method is called from the main thread.
        """
        return (self.object_space is self.core.current_context.object_space and
                threading.current_thread() is threading.main_thread())

    def _safe_to_operate_on(self) -> bool:
        """Check whether it is safe to interact with this context.

        This is considered to be the case if it's the current context and this
        method is called from the main thread.
        """
        return self.core.current_context is self and threading.current_thread() is threading.main_thread()

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
            self.glDeleteTextures(1, GLuint(texture_id))
        else:
            self.object_space.doomed_textures.append(texture_id)

    def delete_buffer(self, buffer_id: int) -> None:
        """Safely delete a Buffer belonging to this context's object space.

        This method behaves similarly to ``delete_texture``, though for
        ``glDeleteBuffers`` instead of ``glDeleteTextures``.
        """
        if self._safe_to_operate_on_object_space():
            self.glDeleteBuffers(1, GLuint(buffer_id))
        else:
            self.object_space.doomed_buffers.append(buffer_id)

    def delete_shader_program(self, program_id: int) -> None:
        """Safely delete a ShaderProgram belonging to this context's object space.

        This method behaves similarly to ``delete_texture``, though for
        ``glDeleteProgram`` instead of ``glDeleteTextures``.
        """
        if self._safe_to_operate_on_object_space():
            self.glDeleteProgram(GLuint(program_id))
        else:
            self.object_space.doomed_shader_programs.append(program_id)

    def delete_shader(self, shader_id: int) -> None:
        """Safely delete a Shader belonging to this context's object space.

        This method behaves similarly to ``delete_texture``, though for
        ``glDeleteShader`` instead of ``glDeleteTextures``.
        """
        if self._safe_to_operate_on_object_space():
            self.glDeleteShader(GLuint(shader_id))
        else:
            self.object_space.doomed_shaders.append(shader_id)

    def delete_renderbuffer(self, rbo_id: int) -> None:
        """Safely delete a Renderbuffer belonging to this context's object space.

        This method behaves similarly to ``delete_texture``, though for
        ``glDeleteRenderbuffers`` instead of ``glDeleteTextures``.
        """
        if self._safe_to_operate_on_object_space():
            self.glDeleteRenderbuffers(1, GLuint(rbo_id))
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
            self.glDeleteVertexArrays(1, GLuint(vao_id))
        else:
            self.doomed_vaos.append(vao_id)

    def delete_framebuffer(self, fbo_id: int) -> None:
        """Safely delete a Framebuffer Object belonging to this context.

        This method behaves similarly to ``delete_vao``, though for
        ``glDeleteFramebuffers`` instead of ``glDeleteVertexArrays``.
        """
        if self._safe_to_operate_on():
            self.glDeleteFramebuffers(1, GLuint(fbo_id))
        else:
            self.doomed_framebuffers.append(fbo_id)

    def get_info(self) -> gl_info.GLInfo:
        """Get the :py:class:`~GLInfo` instance for this context."""
        return self._info

    def _get_uniform_func_tables(self):
        _uniform_getters: dict[GLDataType, Callable] = {
            gl.GLint: self.glGetUniformiv,
            gl.GLfloat: self.glGetUniformfv,
            gl.GLboolean: self.glGetUniformiv,
        }

        _uniform_setters: dict[int, tuple[GLDataType, GLFunc, GLFunc, int]] = {
            # uniform:    gl_type, legacy_setter, setter, length
            gl.GL_BOOL: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_BOOL_VEC2: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 2),
            gl.GL_BOOL_VEC3: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 3),
            gl.GL_BOOL_VEC4: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 4),

            gl.GL_INT: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_INT_VEC2: (gl.GLint, self.glUniform2iv, self.glProgramUniform2iv, 2),
            gl.GL_INT_VEC3: (gl.GLint, self.glUniform3iv, self.glProgramUniform3iv, 3),
            gl.GL_INT_VEC4: (gl.GLint, self.glUniform4iv, self.glProgramUniform4iv, 4),

            gl.GL_FLOAT: (gl.GLfloat, self.glUniform1fv, self.glProgramUniform1fv, 1),
            gl.GL_FLOAT_VEC2: (gl.GLfloat, self.glUniform2fv, self.glProgramUniform2fv, 2),
            gl.GL_FLOAT_VEC3: (gl.GLfloat, self.glUniform3fv, self.glProgramUniform3fv, 3),
            gl.GL_FLOAT_VEC4: (gl.GLfloat, self.glUniform4fv, self.glProgramUniform4fv, 4),

            # 1D Samplers
            gl.GL_SAMPLER_1D: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_SAMPLER_1D_ARRAY: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_INT_SAMPLER_1D: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_INT_SAMPLER_1D_ARRAY: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_1D: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_1D_ARRAY: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),

            # 2D Samplers
            gl.GL_SAMPLER_2D: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_SAMPLER_2D_ARRAY: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_INT_SAMPLER_2D: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_INT_SAMPLER_2D_ARRAY: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_2D: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_2D_ARRAY: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            # Multisample
            gl.GL_SAMPLER_2D_MULTISAMPLE: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_INT_SAMPLER_2D_MULTISAMPLE: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),

            # Cube Samplers
            gl.GL_SAMPLER_CUBE: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_INT_SAMPLER_CUBE: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_CUBE: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_SAMPLER_CUBE_MAP_ARRAY: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_INT_SAMPLER_CUBE_MAP_ARRAY: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_CUBE_MAP_ARRAY: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),

            # 3D Samplers
            gl.GL_SAMPLER_3D: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_INT_SAMPLER_3D: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_UNSIGNED_INT_SAMPLER_3D: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),

            gl.GL_FLOAT_MAT2: (gl.GLfloat, self.glUniformMatrix2fv, self.glProgramUniformMatrix2fv, 4),
            gl.GL_FLOAT_MAT3: (gl.GLfloat, self.glUniformMatrix3fv, self.glProgramUniformMatrix3fv, 6),
            gl.GL_FLOAT_MAT4: (gl.GLfloat, self.glUniformMatrix4fv, self.glProgramUniformMatrix4fv, 16),

            # TODO: test/implement these:
            # GL_FLOAT_MAT2x3: glUniformMatrix2x3fv, glProgramUniformMatrix2x3fv,
            # GL_FLOAT_MAT2x4: glUniformMatrix2x4fv, glProgramUniformMatrix2x4fv,
            # GL_FLOAT_MAT3x2: glUniformMatrix3x2fv, glProgramUniformMatrix3x2fv,
            # GL_FLOAT_MAT3x4: glUniformMatrix3x4fv, glProgramUniformMatrix3x4fv,
            # GL_FLOAT_MAT4x2: glUniformMatrix4x2fv, glProgramUniformMatrix4x2fv,
            # GL_FLOAT_MAT4x3: glUniformMatrix4x3fv, glProgramUniformMatrix4x3fv,

            gl.GL_IMAGE_1D: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_IMAGE_2D: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 2),
            gl.GL_IMAGE_2D_RECT: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 3),
            gl.GL_IMAGE_3D: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 3),

            gl.GL_IMAGE_1D_ARRAY: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 2),
            gl.GL_IMAGE_2D_ARRAY: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 3),

            gl.GL_IMAGE_2D_MULTISAMPLE: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 2),
            gl.GL_IMAGE_2D_MULTISAMPLE_ARRAY: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 3),

            gl.GL_IMAGE_BUFFER: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 3),
            gl.GL_IMAGE_CUBE: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 1),
            gl.GL_IMAGE_CUBE_MAP_ARRAY: (gl.GLint, self.glUniform1iv, self.glProgramUniform1iv, 3),
        }
        return _uniform_getters, _uniform_setters
