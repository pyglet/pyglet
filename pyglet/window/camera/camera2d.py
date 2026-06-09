"""2D camera implementations."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

from pyglet.math import Mat4, Vec2, Vec3, Vec4, clamp

from .base import (
    BaseCamera,
    CameraScissor,
    CameraViewStorage,
    ViewportType,
    _CameraViewBase,
)

if TYPE_CHECKING:
    from pyglet.graphics.shader import UniformBlock
    from pyglet.window import Window


class Camera2DView(_CameraViewBase):
    """A per-camera 2D view node."""

    def __init__(
        self,
        camera: Camera2D,
        storage: CameraViewStorage | None,
        *,
        parent: Camera2DView | None = None,
    ) -> None:
        super().__init__(camera, storage, parent=parent)
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._zoom = 1.0
        self._local_matrix = Mat4()
        self._world_matrix = Mat4()
        self._local_dirty = True
        self._viewport_size: tuple[int, int] | None = None

    @property
    def offset_x(self) -> float:
        return self._offset_x

    @offset_x.setter
    def offset_x(self, value: float) -> None:
        self._offset_x = float(value)
        self._mark_local_dirty()

    @property
    def offset_y(self) -> float:
        return self._offset_y

    @offset_y.setter
    def offset_y(self, value: float) -> None:
        self._offset_y = float(value)
        self._mark_local_dirty()

    @property
    def zoom(self) -> float:
        return self._zoom

    @zoom.setter
    def zoom(self, value: float) -> None:
        camera = self._camera
        self._zoom = clamp(value, camera.min_zoom, camera.max_zoom)
        self._mark_local_dirty()

    @property
    def position(self) -> Vec2:
        return Vec2(self.offset_x, self.offset_y)

    @position.setter
    def position(self, value: tuple[float, float] | Vec2) -> None:
        self.offset_x = value[0]
        self.offset_y = value[1]

    def move(self, axis_x: float, axis_y: float) -> None:
        camera = self._camera
        self.offset_x += camera.scroll_speed * axis_x
        self.offset_y += camera.scroll_speed * axis_y

    def set_scissor_area_relative(self, x: int, y: int, width: int, height: int) -> CameraScissor:
        """Set a view-relative scissor area.

        Unlike ``set_scissor_area`` (window-space), this scissor
        follows the view's transform. This is useful for moving UI panels,
        nested clipped views, and other cases where clipping should travel
        with the view.
        """
        scissor = _RelativeCamera2DScissor(self, x, y, width, height)
        self.set_scissor(scissor)
        return scissor

    def _mark_local_dirty(self) -> None:
        self._local_dirty = True
        self._mark_world_dirty()

    def _local_matrix_cached(self, viewport_size: tuple[int, int]) -> Mat4:
        if self.parent is None and self._viewport_size != viewport_size:
            self._viewport_size = viewport_size
            self._local_dirty = True

        if self._local_dirty:
            camera = self._camera
            if self.parent is None:
                self._local_matrix = camera._compose_root_view_matrix(self, viewport_size[0], viewport_size[1])
            else:
                self._local_matrix = camera._compose_local_view_matrix(self)
            self._local_dirty = False
        return self._local_matrix

    def _world_matrix_cached(self, viewport_size: tuple[int, int]) -> Mat4:
        if self._world_dirty:
            local_matrix = self._local_matrix_cached(viewport_size)
            if self.parent is None:
                self._world_matrix = local_matrix
            else:
                self._world_matrix = self.parent._world_matrix_cached(viewport_size) @ local_matrix
            self._world_dirty = False
        return self._world_matrix


class Camera2D(BaseCamera[Camera2DView]):
    """A scoped 2D camera."""

    def __init__(
        self,
        window: Window,
        *,
        scroll_speed: float = 1.0,
        min_zoom: float = 1.0,
        max_zoom: float = 4.0,
        zoom_speed: float = 1.0,
        viewport: ViewportType | None = None,
        window_block: UniformBlock | None = None,
        copies_per_resource: int = 3,
        projection_uniform: str = "u_projection",
        view_uniform: str = "u_view",
    ) -> None:
        assert min_zoom <= max_zoom, "Minimum zoom must not be greater than maximum zoom."

        view_storage = self._create_default_view_storage(
            window_block=window_block,
            copies_per_resource=copies_per_resource,
            projection_uniform=projection_uniform,
            view_uniform=view_uniform,
        )
        super().__init__(
            window,
            view_storage,
            viewport=viewport,
        )

        self.scroll_speed = scroll_speed
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.zoom_speed = zoom_speed
        self._centered_origin = False
        self._auto_projection = True

        self.view = Camera2DView(self, self.view_storage, parent=None)

        width, height = self._window.get_size()
        self._projection_matrix = Mat4.orthogonal_projection(0, max(width, 1), 0, max(height, 1), -8192, 8192)
        self._view_matrix = Mat4()

    @property
    def projection(self) -> Mat4:
        if self._projection_dirty or self._projection_matrix is None:
            self._projection_matrix = self._build_projection_matrix(self.view)
            self._projection_dirty = False
        return self._projection_matrix

    @projection.setter
    def projection(self, matrix: Mat4) -> None:
        self._auto_projection = False
        self._projection_matrix = matrix
        self._projection_dirty = False
        self._projection_viewport = None
        if self._apply_changed_cpu_data(self._projection_matrix, self._view_matrix, self.view):
            self._mark_cpu_data_applied(self._projection_matrix, self._view_matrix, self.view)

    @property
    def view_matrix(self) -> Mat4:
        return self._view_matrix

    @view_matrix.setter
    def view_matrix(self, matrix: Mat4) -> None:
        self._view_matrix = matrix
        if self._apply_changed_cpu_data(self._projection_matrix, self._view_matrix, self.view):
            self._mark_cpu_data_applied(self._projection_matrix, self._view_matrix, self.view)

    def _on_viewport_changed(self, view: Camera2DView) -> None:
        if self._auto_projection:
            super()._on_viewport_changed(view)
        view._mark_local_dirty()  # noqa: SLF001

    def _sync_viewport(self) -> None:
        self.view._sync_viewport()  # noqa: SLF001

    def _sync_projection(self) -> None:
        """Keep camera projection in sync with window size when auto-managed."""
        if not self._auto_projection:
            return

        self._mark_projection_dirty()

    def _on_internal_resize(self, width: int, height: int) -> None:  # noqa: ARG002
        self._sync_viewport()
        self._sync_projection()

    def _on_internal_scale(self, scale: float, dpi: int) -> None:  # noqa: ARG002
        self._sync_viewport()
        self._sync_projection()

    def _store_matrices(self, projection: Mat4, view_matrix: Mat4, view: Camera2DView) -> None:  # noqa: ARG002
        self._projection_matrix = projection
        self._view_matrix = view_matrix

    @property
    def offset_x(self) -> float:
        return self.view.offset_x

    @offset_x.setter
    def offset_x(self, value: float) -> None:
        self.view.offset_x = float(value)

    @property
    def offset_y(self) -> float:
        return self.view.offset_y

    @offset_y.setter
    def offset_y(self, value: float) -> None:
        self.view.offset_y = float(value)

    @property
    def zoom(self) -> float:
        return self.view.zoom

    @zoom.setter
    def zoom(self, value: float) -> None:
        self.view.zoom = value

    @property
    def position(self) -> Vec2:
        return self.view.position

    @position.setter
    def position(self, value: tuple[float, float] | Vec2) -> None:
        self.view.position = value

    def move(self, axis_x: float, axis_y: float) -> None:
        self.view.move(axis_x, axis_y)

    def _build_projection_matrix(self, view: Camera2DView) -> Mat4:  # noqa: ARG002
        if not self._auto_projection:
            return self._projection_matrix
        width, height = self._get_viewport_size()
        return Mat4.orthogonal_projection(0, width, 0, height, -255, 255)

    def _compose_root_view_matrix(self, root_view: Camera2DView, width: int, height: int) -> Mat4:  # noqa: ARG002
        x = root_view.offset_x
        y = root_view.offset_y
        if self._centered_origin:
            x -= width * 0.5 / root_view.zoom
            y -= height * 0.5 / root_view.zoom
        view = Mat4().translate(Vec3(-x * root_view.zoom, -y * root_view.zoom, 0))
        return view.scale(Vec3(root_view.zoom, root_view.zoom, 1))

    @staticmethod
    def _compose_local_view_matrix(local_view: Camera2DView) -> Mat4:
        view = Mat4().translate(Vec3(-local_view.offset_x * local_view.zoom, -local_view.offset_y * local_view.zoom, 0))
        return view.scale(Vec3(local_view.zoom, local_view.zoom, 1))

    def _build_view_matrix(self, view: Camera2DView) -> Mat4:
        width, height = self._get_viewport_size()
        return view._world_matrix_cached((width, height))

    def set_centered_origin(self, enabled: bool = True) -> None:
        """Set whether the root camera origin is viewport-centered.

        When enabled, world-space ``(0, 0)`` is drawn at the viewport center.
        When disabled, world-space ``(0, 0)`` is drawn at the viewport lower-left.
        """
        self._centered_origin = bool(enabled)
        self.view._mark_local_dirty()  # noqa: SLF001

    def center_origin(self) -> None:
        """Enable viewport-centered root origin."""
        self.set_centered_origin(True)

    def reset_origin(self) -> None:
        """Restore lower-left root origin."""
        self.set_centered_origin(False)

    def set_scissor_area_relative(self, x: int, y: int, width: int, height: int) -> CameraScissor:
        """Set view-relative scissor clipping on the root view.

        This clipping follows camera/view movement and zoom, and is applied
        automatically for group camera scopes.
        """
        return self.view.set_scissor_area_relative(x, y, width, height)
class _RelativeCamera2DScissor(CameraScissor):
    """Scissor area resolved from a Camera2DView's current transform."""

    __slots__ = ("_view",)

    def __init__(self, view: Camera2DView, x: int, y: int, width: int, height: int) -> None:
        super().__init__(x, y, width, height)
        self._view = weakref.ref(view)

    @property
    def area(self) -> tuple[int, int, int, int]:
        view = self._view()
        if view is None:
            return self.x, self.y, self.width, self.height

        camera = view._camera  # noqa: SLF001
        viewport_x, viewport_y, viewport_width, viewport_height = camera._resolve_viewport(view)  # noqa: SLF001
        world_matrix = view._world_matrix_cached((max(1, int(viewport_width)), max(1, int(viewport_height))))  # noqa: SLF001

        p1 = world_matrix @ Vec4(float(self.x), float(self.y), 0.0, 1.0)
        p2 = world_matrix @ Vec4(float(self.x + self.width), float(self.y + self.height), 0.0, 1.0)

        left = round(min(p1.x, p2.x) + viewport_x)
        bottom = round(min(p1.y, p2.y) + viewport_y)
        width = max(0, round(abs(p2.x - p1.x)))
        height = max(0, round(abs(p2.y - p1.y)))
        return left, bottom, width, height


