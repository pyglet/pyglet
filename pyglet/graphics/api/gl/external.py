"""Use pyglet rendering inside an OpenGL context owned by another framework or toolkit."""
from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING, Callable

import pyglet
from pyglet.enums import GraphicsAPI
from pyglet.graphics import GraphicsIntegrationError
from pyglet.graphics.api.base import NullContext
from pyglet.graphics.api.gl.context import OpenGLSurfaceContext
from pyglet.graphics.api.gl.gl import GLFunctions
from pyglet.graphics.api.gl.lib import create_gl_linker

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pyglet.window.camera.base import BaseCamera


class ExternalOpenGLContext(OpenGLSurfaceContext):
    """Adapt an external OpenGL context without creating a pyglet window.

    Construction does not call the host or issue GL commands. Call ``set_current``
    before creating GPU resources. The source owns native context creation,
    resize, event dispatch and destruction. Use this adapter on the main thread.

    ``camera`` is initially None: configure shader matrices yourself, or assign
    a camera for default batch draws. No GL state is saved/restored automatically.
    """
    _destroyed: bool
    _present: Callable[[], None] | None
    _get_framebuffer: Callable[[], int] | None
    _make_current: Callable[[], object]
    _is_current: Callable[[], bool] | None
    _done_current: Callable[[], None] | None

    camera: BaseCamera | None = None

    def __init__(self, make_current: Callable[[], object], *,
                 is_current: Callable[[], bool] | None = None,
                 done_current: Callable[[], None] | None = None,
                 get_proc_address: Callable[[str], int | None] | None = None,
                 get_framebuffer: Callable[[], int] | None = None,
                 present: Callable[[], None] | None = None,
                 context_share: OpenGLSurfaceContext | None = None) -> None:
        """Initialize an external OpenGL context.

        Args:
            make_current:
                Activate the host context. Raise on failure, or return False.
            is_current:
                Check whether that native context is current. If omitted,
                resource finalizers conservatively defer deletion until set_current.
            done_current:
                Optional host callback to release the native context.
            get_proc_address:
                Optional resolver returning integer GL function addresses.
                If omitted, use pyglet's platform loader. Must resolve core functions
                as well as extensions when supplied.
            get_framebuffer:
                Return the host's current default framebuffer ID. Queried
                on every bind, allows source resizes to replace the framebuffer.
            present:
                Optional swap/presentation callback. Omit when the host presents.
            context_share:
                Another pyglet GL context in the same native share group.
                (This only describes existing sharing; it does not apply sharing.)
        """
        self._check_thread()
        core = pyglet.graphics.api.core
        if pyglet.options.backend not in (GraphicsAPI.OPENGL, GraphicsAPI.OPENGL_ES_3):
            raise GraphicsIntegrationError('ExternalOpenGLContext requires the OpenGL or OpenGL ES 3 backend.')
        if context_share is not None and context_share.core is not core:
            raise GraphicsIntegrationError('Shared contexts must belong to the same graphics backend.')
        super().__init__(core, self, None, context_share=context_share)
        self._make_current = make_current
        self._is_current = is_current
        self._done_current = done_current
        self._get_framebuffer = get_framebuffer
        self._present = present
        self._linker = create_gl_linker(get_proc_address) if get_proc_address is not None else None
        self._destroyed = False

    @staticmethod
    def _check_thread() -> None:
        if threading.current_thread() is not threading.main_thread():
            raise GraphicsIntegrationError('External OpenGL contexts must be used on the main thread.')

    def _initialize_gl_functions(self) -> None:
        if self._linker is None:
            super()._initialize_gl_functions()
        else:
            GLFunctions.__init__(self, self._linker)

    def set_current(self) -> None:
        """Activate the native context, initialize pyglet, and flush deletions."""
        self._check_thread()
        if self._destroyed:
            raise GraphicsIntegrationError('The external OpenGL context adapter has been destroyed.')
        try:
            if self._make_current() is False or (self._is_current is not None and not self._is_current()):
                raise GraphicsIntegrationError('The host failed to make its OpenGL context current.')
            super().set_current()
            self.core._have_context = True  # noqa: SLF001
        except BaseException:
            # The native context may have changed even if initialization failed.
            self.core.current_context = NullContext()
            raise

    def release(self) -> None:
        """Release pyglet's current-context tracking and optionally the host context.

        Without done_current, the native context remains current. This method
        never restores a previously active context. Do not release another adapter.
        """
        if self.core.current_context is not self:
            return
        try:
            if self._done_current is not None and (self._is_current is None or self._is_current()):
                self._done_current()
        finally:
            self.core.current_context = NullContext()

    def __exit__(self, *_args: object) -> None:
        self.release()

    @contextmanager
    def frame(self, *, clear: bool = False) -> Iterator[ExternalOpenGLContext]:
        """Activate and bind the host surface for one frame, then release tracking.

        Begins frame-resource tracking and binds the current default framebuffer.
        Clear explicitly in the body, or pass ``clear=True``. On success, finish
        the frame and call the optional host presentation callback. On failure,
        fence any submitted resources without presenting the partial frame.

        Exit always clears pyglet's current-context tracking. The native context
        is released only if a ``done_current`` callback was supplied. Frames
        cannot be nested, including across contexts. No previous context or GL
        state is restored.
        """
        current = self.core.current_context
        if self.frame_active or (current and current.frame_active):
            raise GraphicsIntegrationError('Frame scopes cannot be nested.')
        try:
            self.frame_begin()
            self.bind_default_framebuffer()
            if clear:
                self.clear()
            yield self
        except BaseException:
            if self.frame_active:
                try:
                    self.frame_submit()
                finally:
                    self.frame_index += 1
                    self._frame_active = False
            raise
        else:
            self.frame_end()
        finally:
            self.release()

    def _safe_to_operate_on(self) -> bool:
        return (not self._destroyed and super()._safe_to_operate_on()
                and self._is_current is not None and self._is_current())

    @property
    def default_framebuffer(self) -> int:
        """Return the current framebuffer, or zero for a native surface."""
        return int(self._get_framebuffer()) if self._get_framebuffer is not None else 0

    def present(self) -> None:
        """Present only when a host presentation callback was supplied."""
        if self._present is not None:
            self._present()

    def destroy(self) -> None:
        """Flush pending resources and detach while the native context still exists.

        This will not destroy the native context, that is up to the owner. Clean up any
        GPU objects prior to calling this method.

        Call this before the host destroys or replaces its context.
        """
        self._check_thread()
        if self._destroyed:
            return
        self.set_current()
        self.frame_resources.delete()
        self.release()
        self.invalidate()

    def invalidate(self) -> None:
        """Detach after native context loss without calling the host or OpenGL.

        Pending GPU deletions cannot be flushed after context loss. Native
        context destruction releases unshared resources; explicitly shared
        resources remain the responsibility of the surviving share group.
        """
        self._check_thread()
        if self._destroyed:
            return
        super().destroy()
        self._frame_active = False
        self._destroyed = True
        del self._make_current
        self._is_current = self._done_current = None
        self._get_framebuffer = self._present = self._linker = None
