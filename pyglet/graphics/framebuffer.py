"""Framebuffer render targets and utilities."""

from __future__ import annotations

from contextlib import AbstractContextManager, ExitStack, contextmanager
from typing import TYPE_CHECKING

import pyglet

from pyglet.enums import AddressMode, ComponentFormat, FramebufferAttachment, GraphicsAPI, TextureFilter

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pyglet.image import ImageData
    from pyglet.graphics.api.base import SurfaceContext
    from pyglet.graphics.texture import Texture
    from pyglet.window.camera.base import BaseCamera


def get_screenshot() -> ImageData:
    """Read the pixel data from the default color buffer into ImageData.

    This provides a simplistic screenshot of the default frame buffer.

    This may be inaccurate if you utilize multiple frame buffers in your program.

    .. versionadded:: 3.0
    """
    raise NotImplementedError


if pyglet.options.backend in (GraphicsAPI.OPENGL, GraphicsAPI.OPENGL_ES_3):
    from pyglet.graphics.api.gl.framebuffer import (
        GLFramebuffer as Framebuffer,
        GLRenderbuffer as Renderbuffer,
        get_screenshot,  # noqa: F401
        get_viewport,
    )
elif pyglet.options.backend in (GraphicsAPI.OPENGL_2, GraphicsAPI.OPENGL_ES_2):
    from pyglet.graphics.api.gl2.framebuffer import (
        GL2Framebuffer as Framebuffer,
        GLRenderbuffer as Renderbuffer,
        get_screenshot,  # noqa: F401
        get_viewport,
    )
elif pyglet.options.backend == GraphicsAPI.WEBGL:
    from pyglet.graphics.api.webgl.framebuffer import (
        WebGLFramebuffer as Framebuffer,
        WebGLRenderbuffer as Renderbuffer,
        get_screenshot,  # noqa: F401
        get_viewport,
    )

class RenderTexture:
    """A reusable texture-backed rendering target.

    Entering the context binds the framebuffer, clears it, installs a camera
    whose viewport matches the texture, and makes that camera the window default
    for ordinary pyglet draw calls. All previous state is restored on exit.

    The generated ``texture`` remains owned by the caller after :meth:`delete`
    releases the framebuffer and optional depth buffer.

    .. versionadded:: 3.0
    """

    def __init__(
        self,
        width: int,
        height: int,
        *,
        clear_color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
        depth: bool = False,
        filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
        address_mode: AddressMode = AddressMode.CLAMP_TO_EDGE,
        camera: BaseCamera | None = None,
        context: SurfaceContext | None = None,
    ) -> None:
        """Create a render target and its color texture.

        Args:
            width:
                Texture width in pixels.
            height:
                Texture height in pixels.
            clear_color:
                RGBA color used whenever the context is entered.
            depth:
                If ``True``, attach a 24-bit depth renderbuffer.
            filters:
                Minification and magnification filters for the color texture.
            address_mode:
                Sampling behavior outside the color texture's normalized bounds.
            camera:
                Optional camera to use while rendering. Its viewport is temporarily
                set to the full texture. A dedicated ``Camera2D`` is created by default.
            context:
                Graphics context that owns the target. The current context is used
                when omitted.
        """
        self.width = int(width)
        self.height = int(height)
        if self.width <= 0 or self.height <= 0:
            raise ValueError("RenderTexture dimensions must be greater than zero.")

        from pyglet.graphics.texture import Texture  # noqa: PLC0415
        from pyglet.window.camera import Camera2D  # noqa: PLC0415

        self.context = context or pyglet.graphics.api.core.current_context
        self.clear_color = clear_color
        self._owns_camera = camera is None
        self._deleted = False
        self._scope: AbstractContextManager[RenderTexture] | None = None

        with ExitStack() as cleanup:
            self.texture: Texture = Texture.create(
                self.width,
                self.height,
                filters=filters,
                address_mode=address_mode,
                context=self.context,
            )
            cleanup.callback(self.texture.delete)

            self.framebuffer = Framebuffer(context=self.context)
            cleanup.callback(self.framebuffer.delete)

            self.camera = camera or Camera2D(
                self.context.window,
                viewport=(0, 0, self.width, self.height),
                register_handlers=False,
            )

            self.depth_buffer = None
            with self.framebuffer:
                self.framebuffer.attach_texture(self.texture)
                if depth:
                    self.depth_buffer = Renderbuffer(
                        self.context,
                        self.width,
                        self.height,
                        component_format=ComponentFormat.D,
                        bit_size=24,
                    )
                    cleanup.callback(self.depth_buffer.delete)
                    self.framebuffer.attach_renderbuffer(
                        self.depth_buffer,
                        attachment=FramebufferAttachment.DEPTH,
                    )
                # Attachment helpers unbind for backwards compatibility.
                self.framebuffer.bind()
                if not self.framebuffer.is_complete:
                    msg = f"Could not create a complete {self.width}x{self.height} render texture framebuffer."
                    raise RuntimeError(msg)

            cleanup.pop_all()

    def __enter__(self) -> RenderTexture:  # noqa: PYI034
        if self._deleted:
            raise RuntimeError("Cannot enter a deleted RenderTexture.")
        if self._scope is not None:
            raise RuntimeError("A RenderTexture cannot enter itself recursively.")

        self._scope = self._render_scope()
        return self._scope.__enter__()

    @contextmanager
    def _render_scope(self) -> Iterator[RenderTexture]:
        try:
            previous_viewport = get_viewport()
            previous_camera = self.context.window.camera
            previous_camera_viewport = None
            previous_camera_auto_viewport = False
            if not self._owns_camera:
                previous_camera_viewport = self.camera.viewport
                previous_camera_auto_viewport = self.camera.view._auto_viewport  # noqa: SLF001

            try:
                if not self._owns_camera:
                    self.camera.viewport = (0, 0, self.width, self.height)
                self.context.window._camera = self.camera  # noqa: SLF001

                with self.framebuffer:
                    self.context.renderer.set_viewport(0, 0, self.width, self.height)
                    self.context.renderer.set_scissor(None)
                    self.framebuffer.clear(self.clear_color)
                    yield self
            finally:
                self.context.window._camera = previous_camera  # noqa: SLF001
                if not self._owns_camera:
                    self.camera.viewport = (
                        None if previous_camera_auto_viewport else previous_camera_viewport
                    )
                self.context.renderer.set_viewport(*previous_viewport)
                self.context.renderer.set_scissor(previous_camera.get_group_scissor_area())
        finally:
            self._scope = None

    def __exit__(self, *args: object) -> None:
        if self._scope is not None:
            self._scope.__exit__(*args)

    def clear(self, color: tuple[float, float, float, float] | None = None) -> None:
        """Clear the render target using ``color`` or the configured ``clear_color``."""
        if self._deleted:
            raise RuntimeError("Cannot clear a deleted RenderTexture.")

        self.framebuffer.clear(self.clear_color if color is None else color)

    def delete(self, *, delete_texture: bool = False) -> None:
        """Release framebuffer resources.

        Args:
            delete_texture:
                Also delete the generated ``texture``. By default it is retained
                so it can continue to be used by sprites, models, or shaders.
        """
        if self._scope is not None:
            self.__exit__(None, None, None)

        if not self._deleted:
            if self.depth_buffer is not None:
                self.depth_buffer.delete()
                self.depth_buffer = None
            self.framebuffer.delete()
            self._deleted = True
        if delete_texture and self.texture.id is not None:
            self.texture.delete()
