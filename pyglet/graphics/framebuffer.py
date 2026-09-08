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
        get_screenshot,
        get_viewport,
    )
elif pyglet.options.backend in (GraphicsAPI.OPENGL_2, GraphicsAPI.OPENGL_ES_2):
    from pyglet.graphics.api.gl2.framebuffer import (
        GL2Framebuffer as Framebuffer,
        GLRenderbuffer as Renderbuffer,
        get_screenshot,
        get_viewport,
    )
elif pyglet.options.backend == GraphicsAPI.WEBGL:
    from pyglet.graphics.api.webgl.framebuffer import (
        WebGLFramebuffer as Framebuffer,
        WebGLRenderbuffer as Renderbuffer,
        get_screenshot,  # noqa: F401
        get_viewport,
    )


class _TextureRenderTargetBase:
    """Shared framebuffer and camera state for texture render targets."""

    def __init__(
        self,
        *,
        clear_color: tuple[float, float, float, float],
        depth: bool,
        camera: BaseCamera | None,
        context: SurfaceContext | None,
    ) -> None:
        from pyglet.window.camera import Camera2D  # noqa: PLC0415

        self.context = context or pyglet.graphics.api.core.current_context
        self.clear_color = clear_color
        self.width = 0
        self.height = 0
        self.texture: Texture | None = None
        self.depth_buffer = None
        self._use_depth = depth
        self._owns_camera = camera is None
        self._deleted = False
        self._scope: AbstractContextManager[_TextureRenderTargetBase] | None = None

        with ExitStack() as cleanup:
            self.framebuffer = Framebuffer(context=self.context)
            cleanup.callback(self.framebuffer.delete)
            self.camera = camera or Camera2D(
                self.context.window,
                viewport=(0, 0, 1, 1),
                register_handlers=False,
            )
            cleanup.pop_all()

    def _attach_texture(self, texture: Texture) -> None:
        """Attach a new color texture, resizing dependent target state."""
        if self._deleted:
            raise RuntimeError("Cannot attach a texture to a deleted render target.")
        if self._scope is not None:
            raise RuntimeError("Cannot replace a render target texture while rendering.")
        if texture.width <= 0 or texture.height <= 0:
            raise ValueError("Render target texture dimensions must be greater than zero.")

        replacement_depth = None
        depth_buffer = self.depth_buffer
        if self._use_depth and (
            depth_buffer is None
            or depth_buffer.width != texture.width
            or depth_buffer.height != texture.height
        ):
            replacement_depth = Renderbuffer(
                texture.width,
                texture.height,
                component_format=ComponentFormat.D,
                bit_size=24,
                context=self.context,
            )
            depth_buffer = replacement_depth

        with ExitStack() as cleanup:
            if replacement_depth is not None:
                cleanup.callback(replacement_depth.delete)
            with self.framebuffer:
                self.framebuffer.attach_texture(texture)
                if depth_buffer is not None:
                    self.framebuffer.attach_renderbuffer(
                        depth_buffer,
                        attachment=FramebufferAttachment.DEPTH,
                    )
                # Attachment helpers unbind for backwards compatibility.
                self.framebuffer.bind()
                if not self.framebuffer.is_complete:
                    msg = f"Could not create a complete {texture.width}x{texture.height} texture framebuffer."
                    raise RuntimeError(msg)
            cleanup.pop_all()

        if replacement_depth is not None:
            if self.depth_buffer is not None:
                self.depth_buffer.delete()
            self.depth_buffer = replacement_depth

        self.texture = texture
        self.width = texture.width
        self.height = texture.height
        if self._owns_camera:
            self.camera.viewport = (0, 0, self.width, self.height)

    def __enter__(self) -> _TextureRenderTargetBase:  # noqa: PYI034
        if self._deleted:
            raise RuntimeError("Cannot enter a deleted render target.")
        if self.texture is None:
            raise RuntimeError("Cannot enter a render target without an attached texture.")
        if self._scope is not None:
            raise RuntimeError("A texture render target cannot enter itself recursively.")

        self._scope = self._render_scope()
        return self._scope.__enter__()

    @contextmanager
    def _render_scope(self) -> Iterator[_TextureRenderTargetBase]:
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
            raise RuntimeError("Cannot clear a deleted render target.")
        if self.texture is None:
            raise RuntimeError("Cannot clear a render target without an attached texture.")

        self.framebuffer.clear(self.clear_color if color is None else color)

    def delete(self) -> None:
        """Release the framebuffer and optional depth buffer."""
        if self._scope is not None:
            self.__exit__(None, None, None)

        if not self._deleted:
            if self.depth_buffer is not None:
                self.depth_buffer.delete()
                self.depth_buffer = None
            self.framebuffer.delete()
            self._deleted = True


class RenderTexture(_TextureRenderTargetBase):
    """A fixed texture-backed rendering target.

    Entering the context binds the framebuffer, clears it, installs a camera
    whose viewport matches the texture, and makes that camera the window default
    for ordinary pyglet draw calls. All previous state is restored on exit.

    The generated ``texture`` remains owned by the caller after :meth:`delete`
    releases the framebuffer and optional depth buffer.

    Creating the target allocates GPU resources, and drawing into it submits
    GPU work. Avoid repeatedly creating short-lived targets in performance
    sensitive code.

    This class is useful for a persistent off-screen surface, such as a
    minimap, post-processing input, or dynamically updated sprite texture::

        target = pyglet.graphics.RenderTexture(512, 512)

        with target:
            scene_batch.draw()

        sprite = pyglet.sprite.Sprite(target.texture)

        # The texture remains usable after the target is deleted.
        target.delete()

    The render target does not switch graphics contexts. When using multiple
    windows, make its owning context current with ``window.switch_to()`` before
    constructing, entering, clearing, or deleting it.

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
                Width of the color texture in pixels.
            height:
                Height of the color texture in pixels.
            clear_color:
                RGBA color used whenever the target is entered.
            depth:
                If ``True``, attach a 24-bit depth renderbuffer.
            filters:
                Minification and magnification filters for the color texture.
            address_mode:
                Sampling behavior outside the color texture's normalized bounds.
            camera:
                Optional camera used while rendering. Its viewport is temporarily
                set to the texture dimensions. A dedicated ``Camera2D`` is
                created by default.
            context:
                Graphics context that owns the target. The current context is
                used when omitted.
        """
        width = int(width)
        height = int(height)
        if width <= 0 or height <= 0:
            raise ValueError("RenderTexture dimensions must be greater than zero.")

        from pyglet.graphics.texture import Texture  # noqa: PLC0415

        super().__init__(
            clear_color=clear_color,
            depth=depth,
            camera=camera,
            context=context,
        )
        with ExitStack() as cleanup:
            cleanup.callback(super().delete)
            texture = Texture.create(
                width,
                height,
                filters=filters,
                address_mode=address_mode,
                context=self.context,
            )
            cleanup.callback(texture.delete)
            self._attach_texture(texture)
            cleanup.pop_all()

    def delete(self, *, delete_texture: bool = False) -> None:
        """Release framebuffer resources.

        Args:
            delete_texture:
                Also delete the generated color texture. By default the texture
                remains available to sprites, models, and shaders.
        """
        texture = self.texture
        super().delete()
        if delete_texture and texture is not None and texture.handle is not None:
            texture.delete()


class TextureRenderTarget(_TextureRenderTargetBase):
    """A reusable framebuffer and camera for rendering independent textures.

    Use :meth:`render_to_texture` for each output. The framebuffer, camera, and
    same-sized depth buffer are retained between calls, while each successful
    scope yields a new caller-owned texture.

    Reuse avoids repeated framebuffer and camera setup, but every output still
    allocates a texture and performs GPU rendering. Generating many textures,
    especially every frame, can remain expensive.

    This avoids repeatedly constructing target state when generating many
    textures, while still allocating a distinct texture for every result::

        target = pyglet.graphics.TextureRenderTarget()
        textures = []

        for batch, width, height in jobs:
            with target.render_to_texture(width, height) as texture:
                batch.draw()
            textures.append(texture)

        target.delete()

        # The returned textures are independent and remain valid.
        for texture in textures:
            texture.delete()

    The render target does not switch graphics contexts. When using multiple
    windows, make its owning context current with ``window.switch_to()`` before
    constructing, rendering with, or deleting it.

    .. versionadded:: 3.0
    """

    def __init__(
        self,
        *,
        clear_color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
        depth: bool = False,
        camera: BaseCamera | None = None,
        context: SurfaceContext | None = None,
    ) -> None:
        """Create a reusable texture render target.

        Args:
            clear_color:
                RGBA color used for every output texture.
            depth:
                If ``True``, attach a 24-bit depth renderbuffer. It is retained
                for outputs of the same size and recreated when the size changes.
            camera:
                Optional camera used while rendering. Its viewport is temporarily
                set to the current output dimensions. A dedicated ``Camera2D`` is
                created by default.
            context:
                Graphics context that owns the target. The current context is
                used when omitted.
        """
        super().__init__(
            clear_color=clear_color,
            depth=depth,
            camera=camera,
            context=context,
        )

    @contextmanager
    def render_to_texture(
        self,
        width: int,
        height: int,
        *,
        filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
        address_mode: AddressMode = AddressMode.CLAMP_TO_EDGE,
    ) -> Iterator[Texture]:
        """Render one scope into a new caller-owned texture.

        The target creates and attaches a texture of the requested size, clears
        it on entry, and restores the previous framebuffer, camera, viewport,
        and scissor state on exit. The framebuffer and camera remain available
        for the next call.

        If drawing raises an exception, the incomplete texture is deleted. On
        success, ownership of the texture passes to the caller.

        Args:
            width:
                Width of the output texture in pixels.
            height:
                Height of the output texture in pixels.
            filters:
                Minification and magnification filters for the output texture.
            address_mode:
                Sampling behavior outside the texture's normalized bounds.

        Yields:
            The newly created output texture.
        """
        width = int(width)
        height = int(height)
        if width <= 0 or height <= 0:
            raise ValueError("Render target texture dimensions must be greater than zero.")

        from pyglet.graphics.texture import Texture  # noqa: PLC0415

        texture = Texture.create(
            width,
            height,
            filters=filters,
            address_mode=address_mode,
            context=self.context,
        )
        succeeded = False
        try:
            self._attach_texture(texture)
            with self:
                yield texture
            succeeded = True
        finally:
            if self.texture is texture:
                self.texture = None
            if not succeeded and texture.handle is not None:
                texture.delete()
