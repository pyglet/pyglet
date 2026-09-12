"""Per-draw configuration and transient rendering context."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from pyglet.graphics.api.base import SurfaceContext



if TYPE_CHECKING:
    from pyglet.graphics.api.base import BackendRenderer
    from pyglet.graphics.shader import ShaderProgram
    from pyglet.graphics.state import CameraScopeProtocol
    from pyglet.window.camera.base import BaseCamera, CameraScissor


class _DefaultCameraMarker:
    """Sentinel requesting the surface context's default camera."""

    __slots__ = ()


_default_camera = _DefaultCameraMarker()


@dataclass(eq=False)
class DrawPass:
    """Resolved rendering state for one ordered submission."""
    framebuffer: object | None
    camera: BaseCamera | _DefaultCameraMarker | None
    viewport: tuple | None
    scissor: CameraScissor | tuple | None
    clear_color: tuple[float, float, float, float]
    order: int = 0
    name: str | None = None

    def resolve(self, ctx: SurfaceContext) -> DrawPass:
        """Resolve the default-camera sentinel for this surface context.

        ``None`` deliberately remains camera-free.  In that case explicit
        viewport and scissor values are still retained, but no camera-derived
        values are supplied.
        """
        camera = ctx.window.camera if isinstance(self.camera, _DefaultCameraMarker) else self.camera
        return replace(
            self,
            camera=camera,
            viewport=self.viewport or (camera.viewport if camera is not None else None),
            scissor=self.scissor or (camera.view.scissor if camera is not None else None),
        )


SurfaceContextT = TypeVar("SurfaceContextT", bound=SurfaceContext)
BackendContextT = TypeVar("BackendContextT")


@dataclass
class DrawContext(Generic[SurfaceContextT, BackendContextT]):
    """Transient context passed to group state during a draw."""
    surface_ctx: SurfaceContextT
    backend_ctx: BackendContextT
    draw_pass: DrawPass
    renderer: BackendRenderer
    camera_stack: list[CameraScopeProtocol] = field(default_factory=list)
    viewport_stack: list = field(default_factory=list)
    scissor_stack: list = field(default_factory=list)
    active_shader_program: ShaderProgram | None = None
    _applied_camera: CameraScopeProtocol | None = None
    _applied_viewport: tuple[int, int, int, int] | None = None

    def __post_init__(self) -> None:
        if not self.camera_stack and self.draw_pass.camera is not None:
            self.camera_stack.append(self.draw_pass.camera)

    @property
    def active_camera(self) -> CameraScopeProtocol:
        return self.camera_stack[-1]

    @property
    def active_viewport(self) -> tuple | None:
        return self.viewport_stack[-1] if self.viewport_stack else None

    @property
    def active_scissor(self) -> tuple | None:
        return self.scissor_stack[-1] if self.scissor_stack else None

    def apply_camera_scope(self, *, commit: bool = True, apply_scissor: bool = True) -> None:
        if not self.camera_stack:
            return
        camera = self.active_camera
        if camera is self._applied_camera:
            return
        camera.begin(draw_context=self, commit=commit)
        self._applied_camera = camera
        self.apply_viewport()
        if apply_scissor:
            self.apply_scissor()

    def apply_viewport(self) -> None:
        viewport_state = self.active_viewport
        if viewport_state is not None:
            viewport = (viewport_state.x, viewport_state.y, viewport_state.width, viewport_state.height)
        else:
            viewport = self.active_camera.viewport if self.camera_stack else self.draw_pass.viewport
        if viewport is None:
            return
        resolved_viewport = tuple(map(int, viewport))
        if resolved_viewport == self._applied_viewport:
            return
        self.renderer.set_viewport(*resolved_viewport)
        self._applied_viewport = resolved_viewport

    def apply_scissor(self) -> None:
        scissor_state = self.active_scissor
        if scissor_state is not None:
            scissor = scissor_state.scissor
        else:
            scissor = self.active_camera.get_group_scissor_area() if self.camera_stack else None
            if scissor is None:
                scissor = self.draw_pass.scissor
        self.renderer.set_scissor(scissor)

    def apply_clear_color(self, r: float, g: float, b: float, a: float) -> None:
        self.renderer.set_clear_color(r, g, b, a)

    def begin(self) -> None:
        self.apply_clear_color(*self.draw_pass.clear_color)
        self.apply_camera_scope()
