import weakref

from enum import Enum
from typing import Tuple

import pyglet

from pyglet import gl
from pyglet.gl import gl_info


class OpenGLAPI(Enum):
    OPENGL = 1
    OPENGL_ES = 2


class Config:
    """Graphics configuration.

    A Config stores the preferences for OpenGL attributes such as the
    number of auxiliary buffers, size of the colour and depth buffers,
    double buffering, stencilling, multi- and super-sampling, and so on.

    Different platforms support a different set of attributes, so these
    are set with a string key and a value which is integer or boolean.

    :Ivariables:
        `double_buffer` : bool
            Specify the presence of a back-buffer for every color buffer.
        `stereo` : bool
            Specify the presence of separate left and right buffer sets.
        `buffer_size` : int
            Total bits per sample per color buffer.
        `aux_buffers` : int
            The number of auxiliary color buffers.
        `sample_buffers` : int
            The number of multisample buffers.
        `samples` : int
            The number of samples per pixel, or 0 if there are no multisample
            buffers.
        `red_size` : int
            Bits per sample per buffer devoted to the red component.
        `green_size` : int
            Bits per sample per buffer devoted to the green component.
        `blue_size` : int
            Bits per sample per buffer devoted to the blue component.
        `alpha_size` : int
            Bits per sample per buffer devoted to the alpha component.
        `depth_size` : int
            Bits per sample in the depth buffer.
        `stencil_size` : int
            Bits per sample in the stencil buffer.
        `accum_red_size` : int
            Bits per pixel devoted to the red component in the accumulation
            buffer.
        `accum_green_size` : int
            Bits per pixel devoted to the green component in the accumulation
            buffer.
        `accum_blue_size` : int
            Bits per pixel devoted to the blue component in the accumulation
            buffer.
        `accum_alpha_size` : int
            Bits per pixel devoted to the alpha component in the accumulation
            buffer.
    """

    _attribute_names = [
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
        'debug'
    ]

    major_version = None
    minor_version = None
    forward_compatible = None
    opengl_api = None
    debug = None

    def __init__(self, **kwargs):
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

    def get_gl_attributes(self):
        """Return a list of attributes set on this config.

        :rtype: list of tuple (name, value)
        :return: All attributes, with unset attributes having a value of
            ``None``.
        """
        return [(name, getattr(self, name)) for name in self._attribute_names]

    def match(self, canvas):
        """Return a list of matching complete configs for the given canvas.

        .. versionadded:: 1.2

        :Parameters:
            `canvas` : `Canvas`
                Display to host contexts created from the config.

        :rtype: list of `CanvasConfig`
        """
        raise NotImplementedError('abstract')

    def create_context(self, share):
        """Create a GL context that satisifies this configuration.

        :deprecated: Use `CanvasConfig.create_context`.

        :Parameters:
            `share` : `Context`
                If not None, a context with which to share objects with.

        :rtype: `Context`
        :return: The new context.
        """
        raise gl.ConfigException('This config cannot be used to create contexts.  '
                                 'Use Config.match to created a CanvasConfig')

    def is_complete(self):
        """Determine if this config is complete and able to create a context.

        Configs created directly are not complete, they can only serve
        as templates for retrieving a supported config from the system.
        For example, `pyglet.window.Screen.get_matching_configs` returns
        complete configs.

        :deprecated: Use ``isinstance(config, CanvasConfig)``.

        :rtype: bool
        :return: True if the config is complete and can create a context.
        """
        return isinstance(self, CanvasConfig)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.get_gl_attributes()})"


class CanvasConfig(Config):
    """An OpenGL configuration for a particular canvas.

    Use `Config.match` to obtain an instance of this class.

    .. versionadded:: 1.2

    :Ivariables:
        `canvas` : `Canvas`
            The canvas this config is valid on.

    """

    def __init__(self, canvas, base_config):
        self.canvas = canvas

        self.major_version = base_config.major_version
        self.minor_version = base_config.minor_version
        self.forward_compatible = base_config.forward_compatible
        self.opengl_api = base_config.opengl_api or self.opengl_api
        self.debug = base_config.debug

    def compatible(self, canvas):
        raise NotImplementedError('abstract')

    def create_context(self, share):
        """Create a GL context that satisifies this configuration.

        :Parameters:
            `share` : `Context`
                If not None, a context with which to share objects with.

        :rtype: `Context`
        :return: The new context.
        """
        raise NotImplementedError('abstract')

    def is_complete(self):
        return True


class ObjectSpace:
    def __init__(self):
        # Textures and buffers scheduled for deletion
        # the next time this object space is active.
        self.doomed_textures = []
        self.doomed_buffers = []
        self.doomed_shader_programs = []


class Context:
    """An OpenGL context for drawing.

    Use `CanvasConfig.create_context` to create a context.

    :Ivariables:
        `object_space` : `ObjectSpace`
            An object which is shared between all contexts that share
            GL objects.

    """
    # gl_info.GLInfo instance, filled in on first set_current
    _info = None

    def __init__(self, config, context_share=None):
        self.config = config
        self.context_share = context_share
        self.canvas = None

        self.doomed_vaos = []

        if context_share:
            self.object_space = context_share.object_space
        else:
            self.object_space = ObjectSpace()

        self._cached_programs = weakref.WeakValueDictionary()

    def __repr__(self):
        return f"{self.__class__.__name__}(id={id(self)}, share={self.context_share})"

    def __enter__(self):
        self.set_current()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    def attach(self, canvas):
        if self.canvas is not None:
            self.detach()
        if not self.config.compatible(canvas):
            raise RuntimeError(f'Cannot attach {canvas} to {self}')
        self.canvas = canvas

    def detach(self):
        self.canvas = None

    def set_current(self):
        if not self.canvas:
            raise RuntimeError('Canvas has not been attached')

        # XXX not per-thread
        gl.current_context = self

        # XXX
        gl_info.set_active_context()

        if not self._info:
            self._info = gl_info.GLInfo()
            self._info.set_active_context()

        # Release Textures, Buffers, and VAOs on this context scheduled for
        # deletion. Note that the garbage collector may introduce a race
        # condition, so operate on a copy, and clear the list afterward.
        if self.object_space.doomed_textures:
            textures = self.object_space.doomed_textures[:]
            textures = (gl.GLuint * len(textures))(*textures)
            gl.glDeleteTextures(len(textures), textures)
            self.object_space.doomed_textures.clear()
        if self.object_space.doomed_buffers:
            buffers = self.object_space.doomed_buffers[:]
            buffers = (gl.GLuint * len(buffers))(*buffers)
            gl.glDeleteBuffers(len(buffers), buffers)
            self.object_space.doomed_buffers.clear()
        if self.object_space.doomed_shader_programs:
            for program_id in self.object_space.doomed_shader_programs:
                gl.glDeleteProgram(program_id)
            self.object_space.doomed_shader_programs.clear()
        if self.doomed_vaos:
            vaos = self.doomed_vaos[:]
            vaos = (gl.GLuint * len(vaos))(*vaos)
            gl.glDeleteVertexArrays(len(vaos), vaos)
            self.doomed_vaos.clear()

    def destroy(self):
        """Release the context.

        The context will not be useable after being destroyed.  Each platform
        has its own convention for releasing the context and the buffer(s)
        that depend on it in the correct order; this should never be called
        by an application.
        """
        self.detach()

        if gl.current_context is self:
            gl.current_context = None
            gl_info.remove_active_context()

            # Switch back to shadow context.
            if gl._shadow_window is not None:
                gl._shadow_window.switch_to()

    def create_program(self, *sources: Tuple[str, str], program_class=None):
        """Create a ShaderProgram from OpenGL GLSL source.

        This is a convenience method that takes one or more tuples of
        (source_string, shader_type), and returns a
        :py:class:`~pyglet.graphics.shader.ShaderProgram` instance.

        `source_string` is OpenGL GLSL source code as a str, and `shader_type`
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

        program_class = program_class or pyglet.graphics.shader.ShaderProgram
        shaders = (pyglet.graphics.shader.Shader(src, srctype) for (src, srctype) in sources)
        program = program_class(*shaders)
        self._cached_programs[str(sources)] = program

        return program

    def delete_texture(self, texture_id):
        """Safely delete a Texture belonging to this context.

        Usually, the Texture is released immediately using
        ``glDeleteTextures``, however if another context that does not share
        this context's object space is currently active, the deletion will
        be deferred until an appropriate context is activated.

        :Parameters:
            `texture_id` : int
                The OpenGL name of the Texture to delete.

        """
        if self.object_space is gl.current_context.object_space:
            gl.glDeleteTextures(1, gl.GLuint(texture_id))
        else:
            self.object_space.doomed_textures.append(texture_id)

    def delete_buffer(self, buffer_id):
        """Safely delete a Buffer object belonging to this context.

        This method behaves similarly to `delete_texture`, though for
        ``glDeleteBuffers`` instead of ``glDeleteTextures``.

        :Parameters:
            `buffer_id` : int
                The OpenGL name of the buffer to delete.

        .. versionadded:: 1.1
        """
        if self.object_space is gl.current_context.object_space and False:
            gl.glDeleteBuffers(1, gl.GLuint(buffer_id))
        else:
            self.object_space.doomed_buffers.append(buffer_id)

    def delete_vao(self, vao_id):
        """Safely delete a Vertex Array Object belonging to this context.

        This method behaves similarly to `delete_texture`, though for
        ``glDeleteVertexArrays`` instead of ``glDeleteTextures``.

        :Parameters:
            `vao_id` : int
                The OpenGL name of the Vertex Array to delete.

        .. versionadded:: 2.0
        """
        if gl.current_context is self:
            gl.glDeleteVertexArrays(1, gl.GLuint(vao_id))
        else:
            self.doomed_vaos.append(vao_id)

    def delete_shader_program(self, program_id):
        """Safely delete a Shader Program belonging to this context.

        This method behaves similarly to `delete_texture`, though for
        ``glDeleteProgram`` instead of ``glDeleteTextures``.

        :Parameters:
            `program_id` : int
                The OpenGL name of the Shader Program to delete.

        .. versionadded:: 2.0
        """
        if gl.current_context is self:
            gl.glDeleteProgram(program_id)
        else:
            self.object_space.doomed_shader_programs.append(program_id)

    def get_info(self):
        """Get the OpenGL information for this context.

        .. versionadded:: 1.2

        :rtype: `GLInfo`
        """
        return self._info
