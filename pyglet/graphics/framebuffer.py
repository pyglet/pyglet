from __future__ import annotations

from pyglet.graphics.texture import ColorBufferImage, DepthBufferImage, BufferImageMask


class BufferManagerBase:
    """Manages the set of framebuffers for a context.

    Use :py:func:`~pyglet.image.get_buffer_manager` to obtain the instance
    of this class for the current context.
    """

    def __init__(self):
        self._color_buffer = None
        self._depth_buffer = None
        self.free_stencil_bits = None
        self._refs = []

    @staticmethod
    def get_viewport() -> tuple:
        """Get the current OpenGL viewport dimensions (left, bottom, right, top)."""
        raise NotImplementedError

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
        raise NotImplementedError


def get_buffer_manager() -> BufferManagerBase:
    """Get the buffer manager for the current OpenGL context."""
    raise NotImplementedError
