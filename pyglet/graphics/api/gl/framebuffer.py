"""OpenGL Framebuffer abstractions.

This module provides classes for working with Framebuffers & Renderbuffers
and their attachments. Attachements can be pyglet Texture objects, which allows
easily accessing their data, saving to disk, etc. Renderbuffers can be used
if you don't need to access their data at a later time. For example::

    # Create two objects to use as attachments for our Framebuffer.
    color_buffer = pyglet.graphics.Texture.create(width, height, min_filter=GL_NEAREST, mag_filter=GL_NEAREST)
    depth_buffer = pyglet.image.buffer.Renderbuffer(width, height, GL_DEPTH_COMPONENT)

    # Create a framebuffer object, and attach the two buffers:
    framebuffer = pyglet.image.Framebuffer()
    framebuffer.attach_texture(color_buffer, attachment=GL_COLOR_ATTACHMENT0)
    framebuffer.attach_renderbuffer(depth_buffer, attachment=GL_DEPTH_ATTACHMENT)

    # Bind the Framebuffer, which sets it as the active render target:
    framebuffer.bind()

See the OpenGL documentation for more information on valid attachment types and targets.
"""
from __future__ import annotations

import weakref

import pyglet
from pyglet.graphics import global_backend
from pyglet.graphics.api.gl import GLint, glGetIntegerv, GL_VIEWPORT, glGetFramebufferAttachmentParameteriv, \
    GL_DRAW_FRAMEBUFFER, GL_STENCIL, GL_FRAMEBUFFER_ATTACHMENT_STENCIL_SIZE, GLException, GL_BACK, GLubyte, \
    glReadBuffer, glPixelStorei, GL_PACK_ALIGNMENT, glReadPixels, GL_UNSIGNED_BYTE, GL_RGBA, GL_TEXTURE_2D, \
    glCopyTexSubImage2D, GL_DEPTH_COMPONENT, GL_STENCIL_INDEX, GL_MAX_COLOR_ATTACHMENTS, GLuint, glGenRenderbuffers, \
    glBindRenderbuffer, GL_RENDERBUFFER, glRenderbufferStorageMultisample, glRenderbufferStorage, glDeleteRenderbuffers, \
    GL_FRAMEBUFFER, glGenFramebuffers, glBindFramebuffer, glClear, glDeleteFramebuffers, glCheckFramebufferStatus, \
    GL_FRAMEBUFFER_COMPLETE, GL_FRAMEBUFFER_UNSUPPORTED, GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT, \
    GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT, GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS_EXT, \
    GL_FRAMEBUFFER_INCOMPLETE_FORMATS_EXT, GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER, GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER, \
    GL_COLOR_ATTACHMENT0, glFramebufferTexture, glFramebufferTextureLayer, glFramebufferRenderbuffer
from pyglet.graphics.api.gl.texture import Texture
from pyglet.graphics.framebuffer import BufferManagerBase
from pyglet.image.base import _AbstractImage, ImageData, ImageException
from pyglet.graphics.texture import TextureBase


class BufferManager(BufferManagerBase):
    """Manages the set of framebuffers for a context.

    Use :py:func:`~pyglet.image.get_buffer_manager` to obtain the instance
    of this class for the current context.
    """

    @staticmethod
    def get_viewport() -> tuple:
        """Get the current OpenGL viewport dimensions (left, bottom, right, top)."""
        viewport = (GLint * 4)()
        glGetIntegerv(GL_VIEWPORT, viewport)
        return tuple(viewport)

    def get_color_buffer(self) -> ColorBufferImage:
        """Get the color buffer."""
        viewport = self.get_viewport()
        viewport_width = viewport[2]
        viewport_height = viewport[3]
        if (not self._color_buffer or
                viewport_width != self._color_buffer.width or
                viewport_height != self._color_buffer.height):
            self._color_buffer = ColorBufferImage(*viewport)
        return self._color_buffer

    def get_depth_buffer(self) -> DepthBufferImage:
        """Get the depth buffer."""
        viewport = self.get_viewport()
        viewport_width = viewport[2]
        viewport_height = viewport[3]
        if (not self._depth_buffer or
                viewport_width != self._depth_buffer.width or
                viewport_height != self._depth_buffer.height):
            self._depth_buffer = DepthBufferImage(*viewport)
        return self._depth_buffer

    def get_buffer_mask(self) -> BufferImageMask:
        """Get a free bitmask buffer.

        A bitmask buffer is a buffer referencing a single bit in the stencil
        buffer.  If no bits are free, ``ImageException`` is raised.  Bits are
        released when the bitmask buffer is garbage collected.
        """
        if self.free_stencil_bits is None:
            try:
                stencil_bits = GLint()
                glGetFramebufferAttachmentParameteriv(GL_DRAW_FRAMEBUFFER,
                                                      GL_STENCIL,
                                                      GL_FRAMEBUFFER_ATTACHMENT_STENCIL_SIZE,
                                                      stencil_bits)
                self.free_stencil_bits = list(range(stencil_bits.value))
            except GLException:
                pass

        if not self.free_stencil_bits:
            raise ImageException('No free stencil bits are available.')

        stencil_bit = self.free_stencil_bits.pop(0)
        x, y, width, height = self.get_viewport()
        bufimg = BufferImageMask(x, y, width, height)
        bufimg.stencil_bit = stencil_bit

        def release_buffer(ref, owner=self):
            owner.free_stencil_bits.insert(0, stencil_bit)

        self._refs.append(weakref.ref(bufimg, release_buffer))

        return bufimg


class BufferImage(_AbstractImage):
    """An abstract "default" framebuffer."""

    #: The OpenGL read and write target for this buffer.
    gl_buffer = GL_BACK

    #: The OpenGL format constant for image data.
    gl_format = 0

    #: The format string used for image data.
    format = ''

    owner = None

    def __init__(self, x, y, width, height):
        super().__init__(width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def get_image_data(self):
        buf = (GLubyte * (len(self.format) * self.width * self.height))()

        x = self.x
        y = self.y
        if self.owner:
            x += self.owner.x
            y += self.owner.y

        glReadBuffer(self.gl_buffer)
        glPixelStorei(GL_PACK_ALIGNMENT, 1)
        glReadPixels(x, y, self.width, self.height, self.gl_format, GL_UNSIGNED_BYTE, buf)
        return ImageData(self.width, self.height, self.format, buf)

    def get_region(self, x, y, width, height):
        if self.owner:
            return self.owner.get_region(x + self.x, y + self.y, width, height)

        region = self.__class__(x + self.x, y + self.y, width, height)
        region.gl_buffer = self.gl_buffer
        region.owner = self
        return region

    def get_texture(self) -> TextureBase:
        raise NotImplementedError(f"Not implemented for {self}")

    def get_mipmapped_texture(self) -> TextureBase:
        raise NotImplementedError(f"Not implemented for {self}")

    def blit(self, x: int, y: int, z: int = 0) -> None:
        raise NotImplementedError(f"Not implemented for {self}")

    def upload(self, source, x: int, y: int, z: int) -> None:
        raise NotImplementedError(f"Not implemented for {self}")

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        raise NotImplementedError(f"Not implemented for {self}")


class ColorBufferImage(BufferImage):
    """A color framebuffer.

    This class is used to wrap the primary color buffer (i.e., the back
    buffer)
    """
    gl_format = GL_RGBA
    format = 'RGBA'

    def get_texture(self):
        texture = TextureBase.create(self.width, self.height, GL_TEXTURE_2D, GL_RGBA, blank_data=False)
        self.blit_to_texture(texture.target, texture.level, self.anchor_x, self.anchor_y, 0)
        return texture

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        # TODO: use glCopyTexImage2D if `internalformat` is specified.
        glReadBuffer(self.gl_buffer)
        glCopyTexSubImage2D(target, level, x-self.anchor_x, y-self.anchor_y, self.x, self.y, self.width, self.height)


class DepthBufferImage(BufferImage):
    """The depth buffer.
    """
    gl_format = GL_DEPTH_COMPONENT
    format = 'R'

    def get_texture(self):
        image_data = self.get_image_data()
        return image_data.get_texture()

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        # TODO: use glCopyTexImage2D if `internalformat` is specified.
        glReadBuffer(self.gl_buffer)
        glCopyTexSubImage2D(target, level, x-self.anchor_x, y-self.anchor_y, self.x, self.y, self.width, self.height)


class BufferImageMask(BufferImage):
    """A single bit of the stencil buffer."""
    gl_format = GL_STENCIL_INDEX
    format = 'R'

    # TODO mask methods


def get_buffer_manager() -> BufferManager:
    """Get the buffer manager for the current OpenGL context."""
    context = pyglet.graphics.api.global_backend.current_context
    if not hasattr(context, 'image_buffer_manager'):
        context.image_buffer_manager = BufferManager()
    return context.image_buffer_manager


def get_max_color_attachments() -> int:
    """Get the maximum allow Framebuffer Color attachements."""
    number = GLint()
    glGetIntegerv(GL_MAX_COLOR_ATTACHMENTS, number)
    return number.value


class Renderbuffer:
    """OpenGL Renderbuffer Object."""

    def __init__(self, width: int, height: int, internal_format: int, samples: int = 1) -> None:
        """Create a RenderBuffer instance."""
        self._context = global_backend.current_context
        self._id = GLuint()
        self._width = width
        self._height = height
        self._internal_format = internal_format

        glGenRenderbuffers(1, self._id)
        glBindRenderbuffer(GL_RENDERBUFFER, self._id)

        if samples > 1:
            glRenderbufferStorageMultisample(GL_RENDERBUFFER, samples, internal_format, width, height)
        else:
            glRenderbufferStorage(GL_RENDERBUFFER, internal_format, width, height)

        glBindRenderbuffer(GL_RENDERBUFFER, 0)

    @property
    def id(self) -> int:
        return self._id.value

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def bind(self) -> None:
        glBindRenderbuffer(GL_RENDERBUFFER, self._id)

    @staticmethod
    def unbind() -> None:
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

    def delete(self) -> None:
        glDeleteRenderbuffers(1, self._id)
        self._id = None

    def __del__(self) -> None:
        if self._id is not None:
            try:
                self._context.delete_renderbuffer(self._id.value)
                self._id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id.value})"


class Framebuffer:
    """OpenGL Framebuffer Object.

    .. versionadded:: 2.0
    """
    def __init__(self, target: int = GL_FRAMEBUFFER) -> None:
        """Create a Framebuffer Instance."""
        self._context = pyglet.graphics.api.global_backend.current_context
        self._id = GLuint()
        glGenFramebuffers(1, self._id)
        self._attachment_types = 0
        self._width = 0
        self._height = 0
        self.target = target

    @property
    def id(self) -> int:
        """The Framebuffer id."""
        return self._id.value

    @property
    def width(self) -> int:
        """The width of the widest attachment."""
        return self._width

    @property
    def height(self) -> int:
        """The height of the tallest attachment."""
        return self._height

    def bind(self) -> None:
        """Bind the Framebuffer.

        This ctivates it as the current drawing target.
        """
        glBindFramebuffer(self.target, self._id)

    def unbind(self) -> None:
        """Unbind the Framebuffer.

        Unbind should be called to prevent further rendering
        to the framebuffer, or if you wish to access data
        from its Texture atachments.
        """
        glBindFramebuffer(self.target, 0)

    def clear(self) -> None:
        """Clear the attachments."""
        if self._attachment_types:
            self.bind()
            glClear(self._attachment_types)
            self.unbind()

    def delete(self) -> None:
        """Explicitly delete the Framebuffer."""
        glDeleteFramebuffers(1, self._id)
        self._id = None

    def __del__(self) -> None:
        if self._id is not None:
            try:
                self._context.delete_framebuffer(self._id.value)
                self._id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    @property
    def is_complete(self) -> bool:
        """True if the framebuffer is 'complete', else False."""
        return glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

    @staticmethod
    def get_status() -> str:
        """Get the current Framebuffer status, as a string.

        If ``Framebuffer.is_complete`` is ``False``, this method
        can be used for more information. It will return a
        string with the OpenGL reported status.
        """
        states = {GL_FRAMEBUFFER_UNSUPPORTED: "Framebuffer unsupported. Try another format.",
                  GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT: "Framebuffer incomplete attachment.",
                  GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT: "Framebuffer missing attachment.",
                  GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS_EXT: "Framebuffer unsupported dimension.",
                  GL_FRAMEBUFFER_INCOMPLETE_FORMATS_EXT: "Framebuffer incomplete formats.",
                  GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER: "Framebuffer incomplete draw buffer.",
                  GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER: "Framebuffer incomplete read buffer.",
                  GL_FRAMEBUFFER_COMPLETE: "Framebuffer is complete."}

        gl_status = glCheckFramebufferStatus(GL_FRAMEBUFFER)

        return states.get(gl_status, "Unknown error")

    def attach_texture(self, texture: Texture,
                       target: int = GL_FRAMEBUFFER, attachment: int = GL_COLOR_ATTACHMENT0) -> None:
        """Attach a Texture to the Framebuffer.

        Args:
            texture:
                Specifies the texture object to attach to the framebuffer attachment
                point named by attachment.
            target:
                Specifies the framebuffer target. target must be GL_DRAW_FRAMEBUFFER,
                GL_READ_FRAMEBUFFER, or GL_FRAMEBUFFER. GL_FRAMEBUFFER is equivalent
                to GL_DRAW_FRAMEBUFFER.
            attachment:
                Specifies the attachment point of the framebuffer. attachment must be
                GL_COLOR_ATTACHMENTi, GL_DEPTH_ATTACHMENT, GL_STENCIL_ATTACHMENT or
                GL_DEPTH_STENCIL_ATTACHMENT.
        """
        self.bind()
        glFramebufferTexture(target, attachment, texture.id, texture.level)
        self._attachment_types |= attachment
        self._width = max(texture.width, self._width)
        self._height = max(texture.height, self._height)
        self.unbind()

    def attach_texture_layer(self, texture: Texture, layer: int, level: int,
                             target: int = GL_FRAMEBUFFER, attachment: int = GL_COLOR_ATTACHMENT0) -> None:
        """Attach a Texture layer to the Framebuffer.

        Args:
            texture:
                Specifies the texture object to attach to the framebuffer attachment
                point named by attachment.
            layer:
                Specifies the layer of texture to attach.
            level:
                Specifies the mipmap level of texture to attach.
            target:
                Specifies the framebuffer target. target must be GL_DRAW_FRAMEBUFFER,
                GL_READ_FRAMEBUFFER, or GL_FRAMEBUFFER. GL_FRAMEBUFFER is equivalent
                to GL_DRAW_FRAMEBUFFER.
            attachment:
                Specifies the attachment point of the framebuffer. attachment must be
                GL_COLOR_ATTACHMENTi, GL_DEPTH_ATTACHMENT, GL_STENCIL_ATTACHMENT or
                GL_DEPTH_STENCIL_ATTACHMENT.
        """
        self.bind()
        glFramebufferTextureLayer(target, attachment, texture.id, level, layer)
        self._attachment_types |= attachment
        self._width = max(texture.width, self._width)
        self._height = max(texture.height, self._height)
        self.unbind()

    def attach_renderbuffer(self, renderbuffer: Renderbuffer,
                            target: int = GL_FRAMEBUFFER, attachment: int = GL_COLOR_ATTACHMENT0) -> None:
        """Attach a Renderbuffer to the Framebuffer.

        Args:
            renderbuffer:
                Specifies the Renderbuffer to attach to the framebuffer attachment
                point named by attachment.
            target:
                Specifies the framebuffer target. target must be GL_DRAW_FRAMEBUFFER,
                GL_READ_FRAMEBUFFER, or GL_FRAMEBUFFER. GL_FRAMEBUFFER is equivalent
                to GL_DRAW_FRAMEBUFFER.
            attachment:
                Specifies the attachment point of the framebuffer. attachment must be
                GL_COLOR_ATTACHMENTi, GL_DEPTH_ATTACHMENT, GL_STENCIL_ATTACHMENT or
                GL_DEPTH_STENCIL_ATTACHMENT.
        """
        self.bind()
        glFramebufferRenderbuffer(target, attachment, GL_RENDERBUFFER, renderbuffer.id)
        self._attachment_types |= attachment
        self._width = max(renderbuffer.width, self._width)
        self._height = max(renderbuffer.height, self._height)
        self.unbind()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id.value})"
