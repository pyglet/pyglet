from __future__ import annotations

from types import SimpleNamespace

import pytest

import pyglet
from pyglet.math import Mat4, Vec3
from pyglet.graphics.draw import DrawContext, DrawPass
from pyglet.window.camera import base as camera_base
from pyglet.window.camera.base import (
    BaseCamera,
    CameraViewStorageFactory,
    UniformBufferCameraRegion,
    UniformSetCameraRegion,
)
from tests.annotations import GraphicsAPIGroups, require_graphics_api


def _assert_mat4_close(actual: Mat4, expected: Mat4) -> None:
    for actual_value, expected_value in zip(actual, expected):
        assert actual_value == pytest.approx(expected_value, abs=1e-6)


def _assert_vec3_close(actual: Vec3, expected: Vec3) -> None:
    for actual_value, expected_value in zip(actual, expected):
        assert actual_value == pytest.approx(expected_value, abs=1e-6)


class RecordingStorage:
    def __init__(self, label: str = "root") -> None:
        self.label = label
        self.applies: list[tuple[Mat4, Mat4]] = []
        self.commit_count = 0
        self.bind_count = 0
        self.children: list[RecordingStorage] = []

    def apply(self, projection: Mat4, view: Mat4) -> None:
        self.applies.append((projection, view))

    def commit(self, draw_context) -> None:
        assert draw_context is not None
        self.commit_count += 1

    def bind_camera(self, draw_context) -> None:
        assert draw_context is not None
        self.bind_count += 1

    def create_view_storage(self) -> RecordingStorage:
        child = RecordingStorage(label=f"{self.label}.child{len(self.children)}")
        self.children.append(child)
        return child


class DummyDrawContext:
    active_shader_program = None


class RecordingRenderer:
    def __init__(self) -> None:
        self.viewports: list[tuple[int, int, int, int]] = []
        self.scissors = []
        self.clear_colors = []

    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        self.viewports.append((x, y, width, height))

    def set_scissor(self, scissor) -> None:
        self.scissors.append(scissor)

    def set_clear_color(self, r: float, g: float, b: float, a: float) -> None:
        self.clear_colors.append((r, g, b, a))


def _set_default_view_storage(monkeypatch: pytest.MonkeyPatch, storage: RecordingStorage | UniformSetCameraRegion) -> None:
    monkeypatch.setattr(
        BaseCamera,
        "_create_default_view_storage",
        lambda self, _window, **_kwargs: storage,
    )


@pytest.mark.parametrize("uniform_buffers", [False, True])
def test_default_camera_storage_uniform_buffer_capability(
    monkeypatch: pytest.MonkeyPatch,
    uniform_buffers: bool,
) -> None:
    window = SimpleNamespace(
        context=SimpleNamespace(
            info=SimpleNamespace(features=SimpleNamespace(uniform_buffers=uniform_buffers)),
        ),
    )

    if not uniform_buffers:
        storage = BaseCamera._create_default_view_storage(SimpleNamespace(), window)
        assert isinstance(storage, UniformSetCameraRegion)
        return

    ubo = object()

    class RecordingUniformBufferCameraRegion:
        def __init__(self, *, ubo, copies_per_resource) -> None:
            self.ubo = ubo
            self.copies_per_resource = copies_per_resource

    monkeypatch.setattr(camera_base, "_create_default_camera_ubo", lambda *_args, **_kwargs: ubo)
    monkeypatch.setattr(camera_base, "UniformBufferCameraRegion", RecordingUniformBufferCameraRegion)

    storage = BaseCamera._create_default_view_storage(SimpleNamespace(), window, copies_per_resource=5)

    assert isinstance(storage, RecordingUniformBufferCameraRegion)
    assert storage.ubo is ubo
    assert storage.copies_per_resource == 5


def test_camera2d_auto_viewport_tracks_internal_resize(test_window):
    test_window = test_window
    camera = pyglet.window.camera.Camera2D(test_window)
    framebuffer_width, framebuffer_height = test_window.get_framebuffer_size()

    camera._on_internal_resize(*test_window.get_size())

    assert camera.viewport == (0, 0, framebuffer_width, framebuffer_height)


def test_camera2d_manual_viewport_is_not_overwritten_by_internal_resize(test_window):
    test_window = test_window
    camera = pyglet.window.camera.Camera2D(test_window)
    camera.viewport = (32, 48, 320, 180)

    camera._on_internal_resize(*test_window.get_size())

    assert camera.viewport == (32, 48, 320, 180)


def test_camera2d_root_view_coordinate_conversions(test_window, monkeypatch):
    _set_default_view_storage(monkeypatch, RecordingStorage())
    camera = pyglet.window.camera.Camera2D(test_window)
    camera.viewport = (10, 20, 200, 100)
    camera.position = (5.0, 10.0)
    camera.zoom = 2.0

    _assert_vec3_close(camera.screen_to_viewport(50.0, 60.0), Vec3(40.0, 40.0, 0.0))
    _assert_vec3_close(camera.viewport_to_screen(40.0, 40.0), Vec3(50.0, 60.0, 0.0))
    _assert_vec3_close(camera.world_to_screen(25.0, 30.0), Vec3(50.0, 60.0, 0.0))
    _assert_vec3_close(camera.screen_to_world(50.0, 60.0), Vec3(25.0, 30.0, 0.0))


def test_camera2d_child_view_coordinate_conversions_use_child_viewport(test_window, monkeypatch):
    _set_default_view_storage(monkeypatch, RecordingStorage())
    camera = pyglet.window.camera.Camera2D(test_window)
    camera.viewport = (0, 0, 800, 600)

    child = camera.create_view(inherit=True)
    child.viewport = (100, 200, 300, 150)
    child.position = (10.0, 20.0)

    _assert_vec3_close(child.world_to_screen(25.0, 35.0), Vec3(115.0, 215.0, 0.0))
    _assert_vec3_close(child.screen_to_world(115.0, 215.0), Vec3(25.0, 35.0, 0.0))


def test_camera2d_create_view_inheritance_and_storage_creation(test_window, monkeypatch):
    storage = RecordingStorage()
    _set_default_view_storage(monkeypatch, storage)
    camera = pyglet.window.camera.Camera2D(test_window)

    root_view = camera.view
    inherited = root_view.create_view(inherit=True)
    non_inherited = inherited.create_view(inherit=False)

    assert inherited.parent is root_view
    assert non_inherited.parent is root_view
    assert inherited.storage is not None
    assert non_inherited.storage is not None
    assert inherited.storage is not storage
    assert non_inherited.storage is not inherited.storage


def test_uniform_set_camera_region_creates_per_view_storage(test_window, monkeypatch):
    storage = UniformSetCameraRegion()
    _set_default_view_storage(monkeypatch, storage)
    camera = pyglet.window.camera.Camera2D(test_window)

    child = camera.create_view(inherit=True)

    assert child.storage is not storage
    assert isinstance(child.storage, UniformSetCameraRegion)


def test_camera2d_world_matrix_accumulates_local_and_parent_views(test_window, monkeypatch):
    _set_default_view_storage(monkeypatch, RecordingStorage())
    camera = pyglet.window.camera.Camera2D(test_window)

    root = camera.view
    root.position = (12.0, -6.0)
    root.zoom = 1.5

    child = root.create_view(inherit=True)
    child.position = (3.0, 4.0)
    child.zoom = 0.5

    grandchild = child.create_view(inherit=True)
    grandchild.position = (-2.0, 1.0)
    grandchild.zoom = 2.0

    root_world = camera._build_view_matrix(root)
    child_world = camera._build_view_matrix(child)
    grandchild_world = camera._build_view_matrix(grandchild)

    viewport_width, viewport_height = camera._get_viewport_size()  # noqa: SLF001
    expected_root = camera._compose_root_view_matrix(root, viewport_width, viewport_height)
    expected_child = expected_root @ camera._compose_local_view_matrix(child)
    expected_grandchild = expected_child @ camera._compose_local_view_matrix(grandchild)

    _assert_mat4_close(root_world, expected_root)
    _assert_mat4_close(child_world, expected_child)
    _assert_mat4_close(grandchild_world, expected_grandchild)


def test_camera2d_begin_applies_target_view_storage(test_window, monkeypatch):
    storage = RecordingStorage()
    _set_default_view_storage(monkeypatch, storage)
    camera = pyglet.window.camera.Camera2D(test_window)
    child = camera.create_view(inherit=True)
    assert child.storage is not None

    child.position = (8.0, 5.0)
    child.zoom = 1.25

    camera.begin(child, draw_context=DummyDrawContext())
    camera.end()

    assert len(child.storage.applies) == 1
    assert child.storage.commit_count == 1
    assert len(storage.applies) == 0

    applied_projection, applied_view = child.storage.applies[0]
    _assert_mat4_close(camera.projection, applied_projection)
    _assert_mat4_close(camera.view_matrix, applied_view)


def test_camera2d_begin_bind_does_not_commit_changed_storage(test_window, monkeypatch):
    storage = RecordingStorage()
    _set_default_view_storage(monkeypatch, storage)
    camera = pyglet.window.camera.Camera2D(test_window)
    draw_context = DummyDrawContext()

    camera.begin(draw_context=draw_context)
    camera.end()

    assert len(storage.applies) == 1
    assert storage.commit_count == 1
    assert storage.bind_count == 1

    camera.offset_x = 25.0
    camera.begin(draw_context=draw_context, commit=False)
    camera.end()

    assert len(storage.applies) == 1
    assert storage.commit_count == 1
    assert storage.bind_count == 2


def test_group_camera_viewport_is_applied_to_draw_context_stack(test_window, monkeypatch):
    _set_default_view_storage(monkeypatch, RecordingStorage())
    camera = pyglet.window.camera.Camera2D(test_window)
    camera.viewport = (10, 20, 300, 200)
    child = camera.create_view(inherit=True)
    child.viewport = (30, 40, 160, 90)

    group = pyglet.graphics.Group()
    group.set_camera(child)
    renderer = RecordingRenderer()
    draw_context = DrawContext(
        surface_ctx=test_window.context,
        backend_ctx=None,
        draw_pass=DrawPass(
            framebuffer=None,
            camera=camera,
            viewport=camera.viewport,
            scissor=None,
            clear_color=(0.0, 0.0, 0.0, 1.0),
        ),
        renderer=renderer,
    )

    group.set_state_all(draw_context)

    assert draw_context.camera_stack[-1] is child
    assert renderer.viewports[-1] == (30, 40, 160, 90)


def test_draw_context_skips_unchanged_viewports(test_window, monkeypatch):
    _set_default_view_storage(monkeypatch, RecordingStorage())
    camera = pyglet.window.camera.Camera2D(test_window)
    camera.viewport = (10, 20, 300, 200)
    renderer = RecordingRenderer()
    draw_context = DrawContext(
        surface_ctx=test_window.context,
        backend_ctx=None,
        draw_pass=DrawPass(
            framebuffer=None,
            camera=camera,
            viewport=camera.viewport,
            scissor=None,
            clear_color=(0.0, 0.0, 0.0, 1.0),
        ),
        renderer=renderer,
    )

    draw_context.apply_viewport()
    draw_context.apply_viewport()
    assert renderer.viewports == [(10, 20, 300, 200)]

    camera.viewport = (30, 40, 160, 90)
    draw_context.apply_viewport()
    assert renderer.viewports[-1] == (30, 40, 160, 90)
    assert len(renderer.viewports) == 2


def test_group_camera_scissor_is_applied_once_on_scope_entry(test_window, monkeypatch):
    _set_default_view_storage(monkeypatch, RecordingStorage())
    camera = pyglet.window.camera.Camera2D(test_window)
    child = camera.create_view(inherit=True)
    child.set_scissor_area(10, 20, 300, 200)

    group = pyglet.graphics.Group()
    group.set_camera(child)
    renderer = RecordingRenderer()
    draw_context = DrawContext(
        surface_ctx=test_window.context,
        backend_ctx=None,
        draw_pass=DrawPass(
            framebuffer=None,
            camera=camera,
            viewport=camera.viewport,
            scissor=None,
            clear_color=(0.0, 0.0, 0.0, 1.0),
        ),
        renderer=renderer,
    )

    group.set_state_all(draw_context)

    assert len(renderer.scissors) == 1
    assert renderer.scissors[0].area == (10, 20, 300, 200)


@pytest.mark.parametrize("hide_camera_group", [False, True])
def test_hidden_camera_groups_do_not_apply_camera_or_scissor(
    test_window,
    monkeypatch,
    hide_camera_group: bool,
):
    storage = RecordingStorage()
    _set_default_view_storage(monkeypatch, storage)
    camera = pyglet.window.camera.Camera2D(test_window)
    view = camera.create_view(inherit=True)
    view.set_scissor_area(10, 20, 300, 200)

    camera_group = pyglet.graphics.Group()
    camera_group.set_camera(view)
    image = pyglet.image.ImageData(2, 2, "RGBA", bytes((255, 255, 255, 255)) * 4)
    batch = pyglet.graphics.Batch(context=test_window.context)
    sprite = pyglet.sprite.Sprite(image, batch=batch, group=camera_group)
    (camera_group if hide_camera_group else sprite._group).visible = False  # noqa: SLF001

    batch.draw()

    assert view.storage.commit_count == 0
    assert view.storage.bind_count == 0


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_camera_ubo_views_do_not_overwrite_stable_parent_range(test_window, monkeypatch):
    test_window.switch_to()
    ctx = test_window.context
    ctx.frame_resources.delete()

    monkeypatch.setattr(ctx, "create_frame_fence", object)
    monkeypatch.setattr(ctx, "poll_frame_fence", lambda _fence: True)
    monkeypatch.setattr(ctx, "delete_frame_fence", lambda _fence: None)

    camera = pyglet.window.camera.Camera2D(test_window)
    outer = camera.create_view(inherit=True)
    inner = outer.create_view(inherit=True)
    draw_context = DummyDrawContext()

    try:
        for frame_index, outer_y, inner_x in (
            (0, 0.0, 0.0),
            (1, 75.0, 35.0),
            (2, 150.0, 70.0),
            (3, 225.0, 105.0),
            (4, 300.0, 140.0),
        ):
            ctx.frame_resources.frame_begin(frame_index)
            outer.position = (0.0, outer_y)
            inner.position = (inner_x, 0.0)

            camera.begin(draw_context=draw_context)
            outer.begin(draw_context=draw_context)
            inner.begin(draw_context=draw_context)
            ctx.frame_resources.frame_submit()

        root_storage = camera.view.storage
        outer_storage = outer.storage
        inner_storage = inner.storage

        assert root_storage._current_binding.offset != outer_storage._current_binding.offset  # noqa: SLF001
        assert root_storage._current_binding.offset != inner_storage._current_binding.offset  # noqa: SLF001
        assert outer_storage._current_binding.offset != inner_storage._current_binding.offset  # noqa: SLF001
    finally:
        ctx.frame_resources.delete()


def test_camera2d_scissor_inheritance_intersects_parent_and_child(test_window, monkeypatch):
    _set_default_view_storage(monkeypatch, RecordingStorage())
    camera = pyglet.window.camera.Camera2D(test_window)
    root = camera.view
    root.set_scissor_area(0, 0, 100, 80)

    child = root.create_view(inherit=True)
    child.set_scissor_area(20, 10, 100, 80)

    grandchild = child.create_view(inherit=True)

    child_scissor = child.get_group_scissor_area()
    grandchild_scissor = grandchild.get_group_scissor_area()
    assert child_scissor is not None
    assert grandchild_scissor is not None
    assert child_scissor.area == (20, 10, 80, 70)
    assert grandchild_scissor.area == (20, 10, 80, 70)


def test_camera3d_create_view_inheritance_and_storage_creation(test_window, monkeypatch):
    storage = RecordingStorage()
    _set_default_view_storage(monkeypatch, storage)
    camera = pyglet.window.camera.Camera3D(test_window)

    root_view = camera.view
    inherited = root_view.create_view(inherit=True)
    non_inherited = inherited.create_view(inherit=False)

    assert inherited.parent is root_view
    assert non_inherited.parent is root_view
    assert inherited.storage is not None
    assert non_inherited.storage is not None
    assert inherited.storage is not storage
    assert non_inherited.storage is not inherited.storage


def test_camera3d_world_offset_and_view_matrix_accumulation(test_window, monkeypatch):
    _set_default_view_storage(monkeypatch, RecordingStorage())
    camera = pyglet.window.camera.Camera3D(test_window, position=Vec3(10.0, 20.0, 30.0))

    root = camera.view
    root.offset = Vec3(1.0, 2.0, 3.0)

    child = root.create_view(inherit=True)
    child.offset = Vec3(-2.0, 4.0, 1.0)

    grandchild = child.create_view(inherit=True)
    grandchild.offset = Vec3(3.0, -1.0, 2.0)

    assert root._world_offset_cached() == Vec3(1.0, 2.0, 3.0)  # noqa: SLF001
    assert child._world_offset_cached() == Vec3(-1.0, 6.0, 4.0)  # noqa: SLF001
    assert grandchild._world_offset_cached() == Vec3(2.0, 5.0, 6.0)  # noqa: SLF001

    forward, _, _ = camera._forward_right_up()  # noqa: SLF001
    child_position = camera.position + child._world_offset_cached()  # noqa: SLF001
    grandchild_position = camera.position + grandchild._world_offset_cached()  # noqa: SLF001

    expected_child = Mat4.look_at(child_position, child_position + forward, camera.UP)
    expected_grandchild = Mat4.look_at(grandchild_position, grandchild_position + forward, camera.UP)

    _assert_mat4_close(camera._build_view_matrix(child), expected_child)  # noqa: SLF001
    _assert_mat4_close(camera._build_view_matrix(grandchild), expected_grandchild)  # noqa: SLF001


def test_camera3d_begin_applies_target_view_storage(test_window, monkeypatch):
    storage = RecordingStorage()
    _set_default_view_storage(monkeypatch, storage)
    camera = pyglet.window.camera.Camera3D(test_window, position=Vec3(5.0, 6.0, 7.0))
    child = camera.create_view(inherit=True)
    assert child.storage is not None
    child.offset = Vec3(2.0, 0.0, -3.0)

    camera.begin(child, draw_context=DummyDrawContext())
    camera.end()

    assert len(child.storage.applies) == 1
    assert child.storage.commit_count == 1
    assert len(storage.applies) == 0


def test_camera_factory_default_view_storages_are_created(test_window):
    camera2d = pyglet.window.camera.Camera2D(test_window)
    assert camera2d.view.storage is not None
    camera2d_child = camera2d.create_view(inherit=True)
    assert camera2d_child.storage is not None
    if isinstance(camera2d.view.storage, CameraViewStorageFactory):
        assert camera2d_child.storage is not camera2d.view.storage

    camera3d = pyglet.window.camera.Camera3D(test_window)
    assert camera3d.view.storage is not None
    camera3d_child = camera3d.create_view(inherit=True)
    assert camera3d_child.storage is not None
    if isinstance(camera3d.view.storage, CameraViewStorageFactory):
        assert camera3d_child.storage is not camera3d.view.storage
