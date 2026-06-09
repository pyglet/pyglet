"""3D camera implementations."""

from __future__ import annotations

from math import degrees, radians
from typing import TYPE_CHECKING, Any

from pyglet.math import Mat4, Vec2, Vec3, clamp

from .base import (
    BaseCamera,
    CameraViewStorage,
    ViewportType,
    _CameraViewBase,
)

if TYPE_CHECKING:
    from pyglet.graphics.shader import UniformBlock
    from pyglet.window import Window


class Camera3DView(_CameraViewBase):
    """A per-camera 3D view node."""

    __slots__ = ("_offset", "_world_offset")

    def __init__(
        self,
        camera: Camera3D,
        storage: CameraViewStorage,
        *,
        parent: Camera3DView | None = None,
    ) -> None:
        super().__init__(camera, storage, parent=parent)
        self._offset = Vec3()
        self._world_offset = Vec3()

    @property
    def position(self) -> Vec3:
        return self.offset

    @position.setter
    def position(self, value: tuple[float, float, float] | Vec3) -> None:
        self.offset = Vec3(float(value[0]), float(value[1]), float(value[2]))

    @property
    def offset(self) -> Vec3:
        return self._offset

    @offset.setter
    def offset(self, value: Vec3 | tuple[float, float, float]) -> None:
        self._offset = Vec3(float(value[0]), float(value[1]), float(value[2]))
        self._mark_world_dirty()

    def move(self, axis_x: float, axis_y: float, axis_z: float) -> None:
        camera = self._camera
        self.offset += Vec3(axis_x, axis_y, axis_z) * camera.walk_speed

    def _world_offset_cached(self) -> Vec3:
        if self._world_dirty:
            if self.parent is None:
                self._world_offset = self.offset
            else:
                self._world_offset = self.parent._world_offset_cached() + self.offset
            self._world_dirty = False
        return self._world_offset


class Camera3D(BaseCamera[Camera3DView]):
    """A scoped 3D camera with configurable movement and look vectors."""

    UP = Vec3(0.0, 1.0, 0.0)

    __slots__ = (
        "_far",
        "_field_of_view",
        "_near",
        "_pitch",
        "_position",
        "_roll",
        "_yaw",
        "look_speed",
        "walk_speed",
    )

    def __init__(
        self,
        window: Window,
        *,
        position: Vec3 | None = None,
        target: Vec3 | None = None,
        near: float = 0.1,
        far: float = 1000.0,
        field_of_view: float = 60.0,
        walk_speed: float = 10.0,
        look_speed: float = 10.0,
        viewport: ViewportType | None = None,
        window_block: UniformBlock | None = None,
        copies_per_resource: int = 3,
        projection_uniform: str = "u_projection",
        view_uniform: str = "u_view",
    ) -> None:
        """Initialize a 3D camera.

        Args:
            window:
                Window that this camera controls.
            position:
                World-space camera position.
            target:
                Optional look target used to initialize yaw/pitch.
            near:
                Near clip distance.
            far:
                Far clip distance.
            field_of_view:
                Vertical field of view in degrees.
            walk_speed:
                Translation speed scalar.
            look_speed:
                Look-speed scalar for mouse/controller rotation input.
            viewport:
                Optional fixed viewport override.
            window_block:
                Optional explicit ``WindowBlock`` used for default UBO storage.
            copies_per_resource:
                Number of buffered matrix copies for default UBO storage.
            projection_uniform:
                Projection uniform name for default GL2 storage.
            view_uniform:
                View uniform name for default GL2 storage.
        """
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
        assert self.view_storage is not None
        self._position = position or Vec3()
        self.view = Camera3DView(self, self.view_storage, parent=None)

        self._near = near
        self._far = far
        self._field_of_view = field_of_view
        self.walk_speed = walk_speed
        self.look_speed = look_speed

        self._pitch = 0.0
        self._yaw = -90.0
        self._roll = 0.0

        if target is None:
            target = self.position + Vec3(0.0, 0.0, -1.0)
        self.teleport(self.position, target)

    @property
    def position(self) -> Vec3:
        return self._position

    @position.setter
    def position(self, value: Vec3 | tuple[float, float, float]) -> None:
        self._position = Vec3(float(value[0]), float(value[1]), float(value[2]))
        self._mark_view_dirty()

    @property
    def near(self) -> float:
        return self._near

    @near.setter
    def near(self, value: float) -> None:
        self._near = float(value)
        self._mark_projection_dirty()

    @property
    def far(self) -> float:
        return self._far

    @far.setter
    def far(self, value: float) -> None:
        self._far = float(value)
        self._mark_projection_dirty()

    @property
    def field_of_view(self) -> float:
        return self._field_of_view

    @field_of_view.setter
    def field_of_view(self, value: float) -> None:
        self._field_of_view = float(value)
        self._mark_projection_dirty()

    @property
    def pitch(self) -> float:
        return self._pitch

    @pitch.setter
    def pitch(self, value: float) -> None:
        self._pitch = clamp(value, -85.0, 85.0)
        self._mark_view_dirty()

    @property
    def yaw(self) -> float:
        return self._yaw

    @yaw.setter
    def yaw(self, value: float) -> None:
        self._yaw = value
        self._mark_view_dirty()

    @property
    def roll(self) -> float:
        return self._roll

    @roll.setter
    def roll(self, value: float) -> None:
        self._roll = value
        self._mark_view_dirty()

    def _get_aspect_ratio(self) -> float:
        width, height = self._get_viewport_size()
        return width / height

    def _build_projection_matrix(self, view: Camera3DView) -> Mat4:  # noqa: ARG002
        return Mat4.perspective_projection(
            self._get_aspect_ratio(),
            z_near=self.near,
            z_far=self.far,
            fov=self.field_of_view,
        )

    def _forward_right_up(self) -> tuple[Vec3, Vec3, Vec3]:
        forward = Vec3.from_pitch_yaw(radians(self.pitch), radians(self.yaw))
        right = forward.cross(self.UP).normalize()
        up = right.cross(forward).normalize()
        return forward, right, up

    def _resolve_view_position(self, view: Camera3DView) -> Vec3:
        return self.position + view._world_offset_cached()

    def _build_view_matrix(self, view: Camera3DView) -> Mat4:
        forward, _, _ = self._forward_right_up()
        position = self._resolve_view_position(view)
        return Mat4.look_at(position, position + forward, self.UP)

    def apply_movement_input(self, movement_2d: Vec2, elevation: float, dt: float) -> None:
        if not (movement_2d or elevation):
            return
        forward, right, up = self._forward_right_up()
        translation = (forward * movement_2d.y) + (right * movement_2d.x)
        self.position += (translation + up * elevation) * (self.walk_speed * dt)

    def teleport(self, position: Vec3, target: Vec3 | None = None) -> None:
        if target is not None:
            direction = (target - position).normalize()
            pitch, yaw = direction.get_pitch_yaw()
            self.yaw = degrees(yaw)
            self.pitch = degrees(pitch)
        self.position = position


class FPSCamera(Camera3D):
    """First-person camera preset built on :class:`Camera3D`."""

    __slots__ = ()

    def __init__(
        self,
        window: Window,
        **kwargs: Any,
    ) -> None:
        super().__init__(window, **kwargs)


class ThirdPersonCamera(Camera3D):
    """Third-person orbit camera that follows a target point."""

    __slots__ = ("distance", "target", "target_height")

    def __init__(
        self,
        window: Window,
        *,
        target: Vec3 | None = None,
        distance: float = 8.0,
        target_height: float = 1.5,
        **kwargs: Any,
    ) -> None:
        self.target = target or Vec3()
        self.distance = distance
        self.target_height = target_height
        super().__init__(window, target=self.target, **kwargs)
        self._update_camera_position()

    def _update_camera_position(self) -> None:
        look_target = self.target + Vec3(0.0, self.target_height, 0.0)
        forward = Vec3.from_pitch_yaw(radians(self.pitch), radians(self.yaw)).normalize()
        self.position = look_target - forward * self.distance

    def _build_view_matrix(self, view: Camera3DView) -> Mat4:
        look_target = self.target + Vec3(0.0, self.target_height, 0.0)
        position = self._resolve_view_position(view)
        return Mat4.look_at(position, look_target, self.UP)

    def apply_movement_input(self, movement_2d: Vec2, elevation: float, dt: float) -> None:
        if movement_2d or elevation:
            yaw_forward = Vec3.from_pitch_yaw(0.0, radians(self.yaw)).normalize()
            right = yaw_forward.cross(self.UP).normalize()
            self.target += ((yaw_forward * movement_2d.y) + (right * movement_2d.x) + (self.UP * elevation)) * (
                self.walk_speed * dt
            )

        self._update_camera_position()
