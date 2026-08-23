"""Shared camera internals for 2D/3D camera modules."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar, overload, runtime_checkable

import pyglet
from pyglet.graphics.buffer import UniformBufferRegion
from pyglet.math import Vec3, Vec4


if TYPE_CHECKING:
    from pyglet.customtypes import ScissorProtocol
    from pyglet.graphics.draw import DrawContext
    from pyglet.math import Mat4
    from pyglet.graphics.buffer import UniformBufferObject
    from pyglet.graphics.shader import ShaderProgram, UniformBlock
    from pyglet.window import Window


ViewportType = tuple[int, int, int, int]
ScissorArea = tuple[int, int, int, int]


def _divide_w(point: Vec4) -> Vec3:
    if point.w == 0:
        return Vec3(point.x, point.y, point.z)
    return Vec3(point.x / point.w, point.y / point.w, point.z / point.w)


class CameraScissor:
    """Mutable scissor rectangle for camera/view group-scoped clipping."""
    x: int
    y: int
    width: int
    height: int

    __slots__ = ("x", "y", "width", "height")

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.x = int(x)
        self.y = int(y)
        self.width = max(0, int(width))
        self.height = max(0, int(height))

    @property
    def area(self) -> ScissorArea:
        return self.x, self.y, self.width, self.height

    def set(self, x: int, y: int, width: int, height: int) -> None:
        """Update this scissor rectangle in place.

        Ensure's integer values for backends.
        """
        self.x = int(x)
        self.y = int(y)
        self.width = max(0, int(width))
        self.height = max(0, int(height))

    def __repr__(self):
        return f"{self.__class__.__name__}(x={self.x}, y={self.y}, width={self.width}, height={self.height})"


@runtime_checkable
class CameraViewStorage(Protocol):
    """Target for camera matrix writes."""

    def apply(self, projection: Mat4, view: Mat4) -> None:
        """Apply camera matrices to this region."""

    def commit(self, draw_context: DrawContext) -> None:
        """Commit staged camera data to GPU-visible state when drawing."""

    def bind_camera(self, draw_context: DrawContext) -> None:
        """Bind or apply committed camera data for drawing."""


@runtime_checkable
class CameraViewStorageFactory(Protocol):
    """Optional extension for storages that allocate per-view storage objects."""

    def create_view_storage(self) -> CameraViewStorage:
        """Create storage for a child camera view."""


ViewT = TypeVar("ViewT", bound="_CameraViewBase")


def _create_default_camera_ubo(
    window_block: UniformBlock | None,
    copies_per_resource: int,
    *,
    camera_name: str,
) -> UniformBufferObject:
    """Create the default camera UBO from the package default shader."""
    if window_block is None:
        default_shader = pyglet.graphics.get_default_shader()
        try:
            window_block = default_shader.uniform_blocks["WindowBlock"]
        except KeyError as exc:  # pragma: no cover - backend-specific guard
            msg = (
                f"{camera_name} requires a shader uniform block named "
                "'WindowBlock' when default UBO camera storage is required."
            )
            raise RuntimeError(msg) from exc

    return window_block.create_ubo(copies_per_resource=copies_per_resource)


class UniformBufferCameraRegion(UniformBufferRegion):
    """Camera storage adapter for UBO-backed data uploads."""

    def __init__(
        self,
        ubo: UniformBufferObject,
        *,
        copies_per_resource: int | None = None,
    ) -> None:
        super().__init__(ubo, copies_per_resource=copies_per_resource)
        self._copies_per_resource = copies_per_resource
        self._dirty = False

    def apply(self, projection: Mat4, view: Mat4) -> None:
        self.data.projection[:] = projection
        self.data.view[:] = view
        self.mark_dirty()

    def commit(self, _draw_context: DrawContext | None = None) -> None:
        super().commit()

    def bind_camera(self, _draw_context: DrawContext) -> None:
        self.bind()

    def create_view_storage(self) -> UniformBufferCameraRegion:
        return UniformBufferCameraRegion(
            ubo=self._ubo,
            copies_per_resource=self._copies_per_resource,
        )


class UniformSetCameraRegion:
    """Region adapter that updates per-program projection/view uniforms."""

    def __init__(
        self,
        *,
        projection_uniform: str = "u_projection",
        view_uniform: str = "u_view",
    ) -> None:
        """Create a per-program uniform camera region.

        Args:
            window:
                Window that this region belongs to controls.
            projection_uniform:
                Uniform name to receive the projection matrix.
            view_uniform:
                Uniform name to receive the view matrix.
        """
        self._projection_uniform = projection_uniform
        self._view_uniform = view_uniform
        self._projection_values: tuple[float, ...] | None = None
        self._view_values: tuple[float, ...] | None = None
        self._dirty = False

    def apply(self, projection: Mat4, view: Mat4) -> None:
        self._projection_values = tuple(projection)
        self._view_values = tuple(view)
        self._dirty = True

    def apply_to_program(
        self,
        program: ShaderProgram,
    ) -> bool:
        uniforms = program.uniforms
        has_projection = self._projection_uniform in uniforms
        has_view = self._view_uniform in uniforms
        if not (has_projection or has_view):
            return False

        assert self._projection_values is not None
        assert self._view_values is not None

        if has_projection:
            program[self._projection_uniform] = self._projection_values
        if has_view:
            program[self._view_uniform] = self._view_values
        return True

    def commit(self, draw_context: DrawContext) -> None:
        self._dirty = False

    def bind_camera(self, draw_context: DrawContext) -> None:
        if draw_context.active_shader_program is not None:
            self.apply_to_program(draw_context.active_shader_program)

    def create_view_storage(self) -> UniformSetCameraRegion:
        return UniformSetCameraRegion(
            projection_uniform=self._projection_uniform,
            view_uniform=self._view_uniform,
        )



class _ResolvedGroupScissor:
    """Proxy scissor object that resolves inherited view scissor intersections."""

    __slots__ = ("_view",)

    def __init__(self, view: _CameraViewBase) -> None:
        self._view = view

    @property
    def area(self) -> ScissorArea:
        resolved = self._view._camera._resolve_scissor_area(self._view)
        if resolved is None:
            return 0, 0, 0, 0
        return resolved


class _CameraViewBase:
    """Base class for per-camera views."""

    __slots__ = (
        "_applied_projection",
        "_applied_view",
        "_auto_viewport",
        "_camera",
        "_children",
        "_group_scissor",
        "_parent",
        "_scissor",
        "_view_dirty",
        "_view_matrix",
        "_viewport",
        "_world_dirty",
        "storage",
    )

    def __init__(
        self,
        camera: BaseCamera[Any],
        storage: CameraViewStorage | None,
        *,
        parent: _CameraViewBase | None = None,
    ) -> None:
        self._camera = camera
        self._parent = parent
        self._children: list[_CameraViewBase] = []
        if parent is not None:
            parent._children.append(self)
        self.storage = storage
        self._scissor: CameraScissor | None = None
        self._group_scissor: _ResolvedGroupScissor | None = None
        self._auto_viewport = False
        self._viewport: ViewportType | None = None
        if parent is None:
            self._auto_viewport = camera._initial_auto_viewport  # noqa: SLF001
            self._viewport = camera._initial_viewport  # noqa: SLF001
        self._world_dirty = True
        self._view_dirty = True
        self._view_matrix: Mat4 | None = None

        # Store the applied matrices, so we know when to actually mark storage dirty.
        self._applied_projection: Mat4 | None = None
        self._applied_view: Mat4 | None = None

    @property
    def parent(self) -> _CameraViewBase | None:
        return self._parent

    @property
    def view(self) -> _CameraViewBase:
        return self

    @property
    def viewport(self) -> ViewportType:
        if self._viewport is None:
            if self.parent is not None:
                return self.parent.viewport
            self._sync_viewport()

        assert self._viewport is not None
        return self._viewport

    @viewport.setter
    def viewport(self, values: ViewportType | None) -> None:
        if values is None:
            if self.parent is not None:
                self._auto_viewport = False
                self._set_viewport(None)
                return

            self._auto_viewport = True
            framebuffer_width, framebuffer_height = self._camera._window.get_framebuffer_size()  # noqa: SLF001
            values = (0, 0, max(1, int(framebuffer_width)), max(1, int(framebuffer_height)))
        else:
            if self.parent is None:
                framebuffer_size = self._camera._window.get_framebuffer_size()  # noqa: SLF001
                if not (self._auto_viewport and tuple(values) == (0, 0, *framebuffer_size)):
                    self._auto_viewport = False

        x, y, width, height = values
        self._set_viewport((int(x), int(y), int(width), int(height)))

    def _set_viewport(self, viewport: ViewportType | None) -> None:
        if self._viewport == viewport:
            return
        self._viewport = viewport
        self._camera._on_viewport_changed(self)  # noqa: SLF001
        for child in self._children:
            if child._viewport is None:
                child._mark_inherited_viewport_dirty()

    def _mark_inherited_viewport_dirty(self) -> None:
        self._camera._on_viewport_changed(self)  # noqa: SLF001
        for child in self._children:
            if child._viewport is None:
                child._mark_inherited_viewport_dirty()

    def _sync_viewport(self) -> None:
        if not self._auto_viewport:
            return
        framebuffer_width, framebuffer_height = self._camera._window.get_framebuffer_size()  # noqa: SLF001
        self._set_viewport((0, 0, max(1, int(framebuffer_width)), max(1, int(framebuffer_height))))

    def screen_to_viewport(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert screen-space coordinates to viewport-local coordinates.

        ``screen`` space uses the same lower-left-origin framebuffer
        coordinate system as viewports and scissors. ``viewport`` space is
        local to this view's viewport, so ``(0, 0)`` is the viewport's
        lower-left corner.

        The returned ``z`` value is unchanged.
        """
        point = Vec3(x, y, z)
        viewport_x, viewport_y, _, _ = self._camera._resolve_viewport(self)  # noqa: SLF001
        return Vec3(point.x - viewport_x, point.y - viewport_y, point.z)

    def viewport_to_screen(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert viewport-local coordinates to screen-space coordinates.

        ``screen`` space uses the same lower-left-origin framebuffer
        coordinate system as viewports and scissors.

        The returned ``z`` value is unchanged.
        """
        point = Vec3(x, y, z)
        viewport_x, viewport_y, _, _ = self._camera._resolve_viewport(self)  # noqa: SLF001
        return Vec3(point.x + viewport_x, point.y + viewport_y, point.z)

    def contains_screen_point(self, x: float, y: float) -> bool:
        """Return whether a screen-space point is inside this view's viewport."""
        viewport_x, viewport_y, viewport_width, viewport_height = self._camera._resolve_viewport(self)  # noqa: SLF001
        return viewport_x <= x <= viewport_x + viewport_width and viewport_y <= y <= viewport_y + viewport_height

    def _viewport_to_clip(self, x: float, y: float, z: float = 0.0) -> Vec3:
        point = Vec3(x, y, z)
        _, _, viewport_width, viewport_height = self._camera._resolve_viewport(self)  # noqa: SLF001
        viewport_width = max(1, int(viewport_width))
        viewport_height = max(1, int(viewport_height))
        return Vec3(
            (point.x / viewport_width) * 2.0 - 1.0,
            (point.y / viewport_height) * 2.0 - 1.0,
            point.z,
        )

    def _clip_to_viewport(self, x: float, y: float, z: float = 0.0) -> Vec3:
        point = Vec3(x, y, z)
        _, _, viewport_width, viewport_height = self._camera._resolve_viewport(self)  # noqa: SLF001
        viewport_width = max(1, int(viewport_width))
        viewport_height = max(1, int(viewport_height))
        return Vec3(
            (point.x + 1.0) * 0.5 * viewport_width,
            (point.y + 1.0) * 0.5 * viewport_height,
            point.z,
        )

    def _screen_to_clip(self, x: float, y: float, z: float = 0.0) -> Vec3:
        point = self.screen_to_viewport(x, y, z)
        return self._viewport_to_clip(point.x, point.y, point.z)

    def _clip_to_screen(self, x: float, y: float, z: float = 0.0) -> Vec3:
        point = self._clip_to_viewport(x, y, z)
        return self.viewport_to_screen(point.x, point.y, point.z)

    @staticmethod
    def _clip_to_projection(x: float, y: float, z: float = 0.0, w: float = 1.0) -> Vec4:
        point = Vec3(x, y, z)
        return Vec4(point.x * w, point.y * w, point.z * w, w)

    @staticmethod
    def _projection_to_clip(x: float, y: float, z: float = 0.0, w: float = 1.0) -> Vec3:
        return _divide_w(Vec4(x, y, z, w))

    def _view_to_projection(self, x: float, y: float, z: float = 0.0, w: float = 1.0) -> Vec4:
        projection, _ = self._camera._get_matrices_for_view(self)  # noqa: SLF001
        return projection @ Vec4(x, y, z, w)

    def _projection_to_view(self, x: float, y: float, z: float = 0.0, w: float = 1.0) -> Vec3:
        projection, _ = self._camera._get_matrices_for_view(self)  # noqa: SLF001
        return _divide_w(~projection @ Vec4(x, y, z, w))

    def _screen_to_projection(self, x: float, y: float, z: float = 0.0, w: float = 1.0) -> Vec4:
        point = self._screen_to_clip(x, y, z)
        return self._clip_to_projection(point.x, point.y, point.z, w)

    def _projection_to_screen(self, x: float, y: float, z: float = 0.0, w: float = 1.0) -> Vec3:
        point = self._projection_to_clip(x, y, z, w)
        return self._clip_to_screen(point.x, point.y, point.z)

    def _world_to_projection(self, x: float, y: float, z: float = 0.0) -> Vec4:
        projection, view_matrix = self._camera._get_matrices_for_view(self)  # noqa: SLF001
        return projection @ view_matrix @ Vec4(x, y, z, 1.0)

    def _projection_to_world(self, x: float, y: float, z: float = 0.0, w: float = 1.0) -> Vec3:
        projection, view_matrix = self._camera._get_matrices_for_view(self)  # noqa: SLF001
        return _divide_w(~view_matrix @ ~projection @ Vec4(x, y, z, w))

    def view_to_screen(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert view-space coordinates to screen-space coordinates."""
        point = self._view_to_projection(x, y, z)
        return self._projection_to_screen(point.x, point.y, point.z, point.w)

    def screen_to_view(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert screen-space coordinates to view-space coordinates.

        ``z`` is the depth in the projection range. Use ``-1`` for the near
        clip plane, ``1`` for the far clip plane, or ``0`` for the middle.
        For 3D picking, call this with ``z=-1`` and ``z=1`` to get points on
        the near and far clip planes.
        """
        point = self._screen_to_projection(x, y, z)
        return self._projection_to_view(point.x, point.y, point.z, point.w)

    def world_to_view(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert world-space coordinates to this view's view space."""
        _, view_matrix = self._camera._get_matrices_for_view(self)  # noqa: SLF001
        return _divide_w(view_matrix @ Vec4(x, y, z, 1.0))

    def view_to_world(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert view-space coordinates to world space."""
        _, view_matrix = self._camera._get_matrices_for_view(self)  # noqa: SLF001
        return _divide_w(~view_matrix @ Vec4(x, y, z, 1.0))

    def world_to_viewport(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert world-space coordinates to viewport-local coordinates."""
        point = self._projection_to_clip(*self._world_to_projection(x, y, z))
        return self._clip_to_viewport(point.x, point.y, point.z)

    def viewport_to_world(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert viewport-local coordinates to world-space coordinates.

        ``z`` is the depth in the projection range. Use ``-1`` for the near
        clip plane, ``1`` for the far clip plane, or ``0`` for the middle.
        """
        point = self._viewport_to_clip(x, y, z)
        projected = self._clip_to_projection(point.x, point.y, point.z)
        return self._projection_to_world(projected.x, projected.y, projected.z, projected.w)

    def world_to_screen(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert world-space coordinates to screen-space coordinates.

        The returned ``x`` and ``y`` are framebuffer coordinates in the same
        lower-left-origin space as the viewport.

        The returned ``z`` is the depth in the projection range.
        """
        point = self._projection_to_clip(*self._world_to_projection(x, y, z))
        return self._clip_to_screen(point.x, point.y, point.z)

    def screen_to_world(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert screen-space coordinates to world-space coordinates.

        ``z`` is the depth in the projection range. For a 2D camera, the
        default ``z=0`` maps to the usual world ``z=0`` plane.

        For 3D, call this with ``z=-1`` and ``z=1`` to get near and far world-space
        points for a ray.
        """
        point = self._screen_to_projection(x, y, z)
        return self._projection_to_world(point.x, point.y, point.z, point.w)

    @property
    def scissor_area(self) -> ScissorArea | None:
        """Optional window-space scissor area for this view."""
        if self._scissor is None:
            return None
        return self._scissor.area

    @property
    def scissor(self) -> CameraScissor | None:
        """Optional mutable scissor descriptor attached to this view."""
        return self._scissor

    def set_scissor_area(self, x: int, y: int, width: int, height: int) -> CameraScissor:
        """Set a window-space scissor area for this view.

        Child views inherit and intersect this area when ``inherit=True``.
        Scissor clipping is used by group camera scopes.

        Returns:
            The scissor area object assigned.
        """
        if self._scissor is None:
            self._scissor = CameraScissor(x, y, width, height)
        else:
            self._scissor.set(x, y, width, height)
        return self._scissor

    def set_scissor(self, scissor: CameraScissor | None) -> None:
        """Attach a mutable scissor object to this view."""
        self._scissor = scissor

    def clear_scissor_area(self) -> None:
        """Disable view-level scissor clipping for this view."""
        self._scissor = None

    def get_group_scissor_area(self) -> ScissorProtocol | None:
        """Resolve effective scissor object for group camera scopes."""
        if self._camera._resolve_scissor_area(self) is None:  # noqa: SLF001
            return None
        if self._group_scissor is None:
            self._group_scissor = _ResolvedGroupScissor(self)
        return self._group_scissor

    def _mark_world_dirty(self) -> None:
        self._world_dirty = True
        self._view_dirty = True
        for child in self._children:
            child._mark_world_dirty()

    def begin(self, *, draw_context: DrawContext, commit: bool = True) -> None:
        self._camera.begin(self, draw_context=draw_context, commit=commit)

    def end(self) -> None:
        self._camera.end()

    def create_view(self, inherit: bool = True) -> _CameraViewBase:
        """Create a child view.

        Args:
            inherit:
                When ``True``, the returned view is parented to this view and
                accumulates this view's transform. When ``False``, the returned
                view is parented to the camera root view.
        """
        camera = self._camera
        parent = self if inherit else camera.view
        child_storage = camera._create_child_view_storage(self.storage)  # noqa: SLF001
        return type(self)(camera, child_storage, parent=parent)


class BaseCamera(Generic[ViewT]):
    """Base class for scoped camera usage.

    A camera scope updates projection/view state in :meth:`begin`.
    :meth:`end` only closes the scope marker and does not restore prior state.

    The ``view`` object stores camera transform inputs (for example offsets and
    zoom), while camera implementations may also keep a separate published
    matrix state. This allows callers to read/set the current camera matrices
    directly (for example through ``window.projection`` / ``window.view``)
    without needing to mutate transform fields on the view object.

    Viewports are stored by camera views. The camera-level ``viewport`` property
    is a convenience proxy for the root view's viewport.
    """

    def __init__(
        self,
        window: Window,
        view_storage: CameraViewStorage | None = None,
        *,
        viewport: ViewportType | None = None,
        register_handlers: bool = True,
    ) -> None:
        """Initialize a camera.

        Args:
            window:
                Window that this camera controls.
            view_storage:
                Target for resolved projection/view matrix writes. If ``None``,
                no output target is applied unless a view provides one.
            viewport:
                Optional fixed viewport for the root view. If ``None``, the
                root view defaults to the full framebuffer viewport and tracks
                resize/scale events.
            register_handlers:
                If ``True``, register the camera for window resize and scale
                events. Disable this for fixed-size offscreen cameras.
        """
        self._window = weakref.proxy(window)

        if not isinstance(view_storage, CameraViewStorage):
            msg = (
                "Camera region must implement apply(projection, view), commit(draw_context), "
                "and bind_camera(draw_context)."
            )
            raise TypeError(msg)

        self.view_storage = view_storage
        self._projection_dirty = True
        self._projection_matrix: Mat4 | None = None
        self._projection_viewport: ViewportType | None = None
        framebuffer_width, framebuffer_height = window.get_framebuffer_size()
        default_viewport = (0, 0, max(1, int(framebuffer_width)), max(1, int(framebuffer_height)))
        self._initial_auto_viewport = viewport is None
        self._initial_viewport = default_viewport if viewport is None else tuple(map(int, viewport))
        self._view: ViewT | None = None

        self._resolved_viewport: tuple[int, int, int, int] | None = None

        if register_handlers:
            window.push_handlers(self)

    def _create_default_view_storage(
        self,
        window: Window,
        *,
        window_block: UniformBlock | None = None,
        copies_per_resource: int = 3,
        projection_uniform: str = "u_projection",
        view_uniform: str = "u_view",
    ) -> CameraViewStorage:
        """Create the root view storage for this camera."""
        if not window.context.info.features.uniform_buffers:
            return UniformSetCameraRegion(
                projection_uniform=projection_uniform,
                view_uniform=view_uniform,
            )

        ubo = _create_default_camera_ubo(
            window_block,
            copies_per_resource,
            camera_name=type(self).__name__,
        )
        return UniformBufferCameraRegion(ubo=ubo, copies_per_resource=copies_per_resource)

    @property
    def viewport(self) -> tuple[int, int, int, int]:
        """Viewport of this camera's root view.

        The viewport is stored on camera views. This property is a convenience
        proxy for ``camera.view.viewport``.
        """
        return self.view.viewport

    @viewport.setter
    def viewport(self, values: tuple[int, int, int, int] | None) -> None:
        self.view.viewport = values

    def screen_to_viewport(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert screen-space coordinates to root-view viewport coordinates."""
        return self.view.screen_to_viewport(x, y, z)

    def viewport_to_screen(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert root-view viewport coordinates to screen-space coordinates."""
        return self.view.viewport_to_screen(x, y, z)

    def contains_screen_point(self, x: float, y: float) -> bool:
        """Return whether a screen-space point is inside the root view's viewport."""
        return self.view.contains_screen_point(x, y)

    def view_to_screen(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert root-view view-space coordinates to screen space."""
        return self.view.view_to_screen(x, y, z)

    def screen_to_view(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert screen-space coordinates to root-view view space."""
        return self.view.screen_to_view(x, y, z)

    def world_to_view(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert world-space coordinates to root-view view space."""
        return self.view.world_to_view(x, y, z)

    def view_to_world(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert root-view view-space coordinates to world space."""
        return self.view.view_to_world(x, y, z)

    def world_to_viewport(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert world-space coordinates to root-view viewport coordinates."""
        return self.view.world_to_viewport(x, y, z)

    def viewport_to_world(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert root-view viewport coordinates to world space."""
        return self.view.viewport_to_world(x, y, z)

    def world_to_screen(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert world-space coordinates to screen space using the root view."""
        return self.view.world_to_screen(x, y, z)

    def screen_to_world(self, x: float, y: float, z: float = 0.0) -> Vec3:
        """Convert screen-space coordinates to world space using the root view."""
        return self.view.screen_to_world(x, y, z)

    def _mark_projection_dirty(self) -> None:
        self._projection_dirty = True

    def _mark_view_dirty(self) -> None:
        self.view._mark_world_dirty()  # noqa: SLF001

    def _on_viewport_changed(self, view: ViewT) -> None:
        """Hook for cameras whose view transform depends on viewport dimensions."""
        _ = view
        self._mark_projection_dirty()

    def _create_child_view_storage(self, parent_storage: CameraViewStorage | None) -> CameraViewStorage | None:
        """Create child-view storage from a parent storage object."""
        if parent_storage is None:
            return None
        if isinstance(parent_storage, CameraViewStorageFactory):
            return parent_storage.create_view_storage()
        return parent_storage

    def _sync_viewport(self) -> None:
        self.view._sync_viewport()  # noqa: SLF001

    def _on_internal_resize(self, width: int, height: int) -> None:
        _ = width, height
        self._sync_viewport()

    def _on_internal_scale(self, scale: float, dpi: int) -> None:
        _ = scale, dpi
        self._sync_viewport()

    def _resolve_viewport(self, view: ViewT | None = None) -> tuple[int, int, int, int]:
        target_view = self.view if view is None else view
        target_view._sync_viewport()  # noqa: SLF001
        return target_view.viewport

    def _get_viewport_size(self) -> tuple[int, int]:
        if self._resolved_viewport is not None:
            return max(1, int(self._resolved_viewport[2])), max(1, int(self._resolved_viewport[3]))
        viewport = self._resolve_viewport()
        return max(1, int(viewport[2])), max(1, int(viewport[3]))

    def _build_projection_matrix(self, view: ViewT) -> Mat4:  # noqa: ARG002
        raise NotImplementedError

    def _build_view_matrix(self, view: ViewT) -> Mat4:
        raise NotImplementedError

    def _get_projection_matrix(self, view: ViewT) -> Mat4:
        viewport = self._resolved_viewport or self._resolve_viewport(view)
        if self._projection_dirty or self._projection_matrix is None or self._projection_viewport != viewport:
            self._projection_matrix = self._build_projection_matrix(view)
            self._projection_viewport = viewport
            self._projection_dirty = False
        return self._projection_matrix

    def _get_view_matrix(self, view: ViewT) -> Mat4:
        if view._view_dirty or view._view_matrix is None:  # noqa: SLF001
            view._view_matrix = self._build_view_matrix(view)  # noqa: SLF001
            view._view_dirty = False  # noqa: SLF001
        return view._view_matrix  # noqa: SLF001

    def _get_matrices_for_view(self, view: ViewT) -> tuple[Mat4, Mat4]:
        """Resolve projection and view matrices using a view's effective viewport."""
        previous_viewport = self._resolved_viewport
        self._resolved_viewport = self._resolve_viewport(view)
        try:
            return self._get_projection_matrix(view), self._get_view_matrix(view)
        finally:
            self._resolved_viewport = previous_viewport

    @property
    def view(self) -> ViewT:
        if self._view is None:
            msg = "Camera root view has not been initialized."
            raise RuntimeError(msg)
        return self._view

    @view.setter
    def view(self, value: ViewT) -> None:
        self._view = value

    @staticmethod
    def _intersect_scissor_areas(a: ScissorArea | None, b: ScissorArea | None) -> ScissorArea | None:
        if a is None:
            return b
        if b is None:
            return a

        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        left = max(ax, bx)
        bottom = max(ay, by)
        right = min(ax + aw, bx + bw)
        top = min(ay + ah, by + bh)
        return left, bottom, max(0, right - left), max(0, top - bottom)

    def _resolve_scissor_area(self, view: ViewT) -> ScissorArea | None:
        scissor: ScissorArea | None = None
        chain: list[_CameraViewBase] = []
        current: _CameraViewBase | None = view
        while current is not None:
            chain.append(current)
            current = current.parent

        for scoped_view in reversed(chain):
            scissor = self._intersect_scissor_areas(scissor, scoped_view.scissor_area)
        return scissor

    def _apply_cpu_data(
        self,
        projection: Mat4,
        view_matrix: Mat4,
        storage: CameraViewStorage | None,
    ) -> None:
        if storage is None:
            return
        storage.apply(projection, view_matrix)

    def _cpu_data_changed(self, projection: Mat4, view_matrix: Mat4, view: ViewT) -> bool:
        return projection != view._applied_projection or view_matrix != view._applied_view  # noqa: SLF001

    def _mark_cpu_data_applied(self, projection: Mat4, view_matrix: Mat4, view: ViewT) -> None:
        view._applied_projection = projection  # noqa: SLF001
        view._applied_view = view_matrix  # noqa: SLF001

    def _apply_changed_cpu_data(self, projection: Mat4, view_matrix: Mat4, view: ViewT) -> bool:
        storage = view.storage
        if storage is None or not self._cpu_data_changed(projection, view_matrix, view):
            return False

        storage.apply(projection, view_matrix)
        return True

    def _store_matrices(self, projection: Mat4, view_matrix: Mat4, view: ViewT) -> None:  # noqa: ARG002
        """Hook for camera implementations that cache resolved matrices.

        Subclasses can persist the final projection/view matrices computed in
        :meth:`begin` as camera-level state for external access.
        """

    @overload
    def begin(self, *, draw_context: DrawContext, commit: bool = True) -> None:
        ...

    @overload
    def begin(self, view: ViewT | None = None, *, draw_context: DrawContext, commit: bool = True) -> None:
        ...

    def begin(self, view: ViewT | None = None, *, draw_context: DrawContext, commit: bool = True) -> None:
        """Apply camera state for one scope.

        Resolves the active view, computes projection/view matrices, optionally
        stores those matrices on the camera, applies them to the view storage,
        and commits the storage for drawing.
        """
        target_view = self.view if view is None else view

        self._resolved_viewport = self._resolve_viewport(target_view)

        projection = self._get_projection_matrix(target_view)
        view_matrix = self._get_view_matrix(target_view)
        self._store_matrices(projection, view_matrix, target_view)

        storage = target_view.storage
        changed = False
        if commit:
            changed = self._apply_changed_cpu_data(projection, view_matrix, target_view)
        if storage is not None and commit:
            storage.commit(draw_context)
        if storage is not None:
            storage.bind_camera(draw_context)
        if changed:
            self._mark_cpu_data_applied(projection, view_matrix, target_view)

    def end(self) -> None:
        self._resolved_viewport = None

    def create_view(
        self,
        inherit: bool = True,
    ) -> ViewT:
        """Create a camera view from this camera's default root view."""
        return self.view.create_view(inherit=inherit)

    def get_group_scissor_area(self) -> ScissorProtocol | None:
        """Resolve effective scissor object for this camera's default view."""
        return self.view.get_group_scissor_area()

    def set_scissor_area(self, x: int, y: int, width: int, height: int) -> CameraScissor:
        """Set scissor clipping on the default root view.

        Note:
            Scissor clipping is applied for group camera scopes
            (``Group.set_camera`` / ``Group.set_camera``). It is not
            applied for direct ``with camera:`` helper scopes.
        """
        return self.view.set_scissor_area(x, y, width, height)

    def set_scissor(self, scissor: CameraScissor | None) -> None:
        """Attach a mutable scissor object to the default root view."""
        self.view.set_scissor(scissor)

    def clear_scissor_area(self) -> None:
        """Clear scissor clipping from the default root view."""
        self.view.clear_scissor_area()

