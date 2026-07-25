import ctypes

import pyglet
import pytest
from pyglet.graphics.buffer import CTypeDataStore
from pyglet.graphics.shader import Attribute
from tests.annotations import GraphicsAPIGroups, require_graphics_api, skip_graphics_api

if pyglet.options.backend in GraphicsAPIGroups.GL3:
    from pyglet.graphics.api.gl.buffer import GLBufferObject, GLIndexedBufferObject, GLMappedBufferObject
elif pyglet.options.backend in GraphicsAPIGroups.GL2:
    from pyglet.graphics.api.gl2.buffer import (
        GL2BufferObject as GLBufferObject,
        GL2IndexedBufferObject as GLIndexedBufferObject,
        GL2MappedBufferObject as GLMappedBufferObject
    )
else:
    pytest.skip(f"Unsupported graphics backend for buffer tests: {pyglet.options.backend}", allow_module_level=True)




def test_ctype_data_store_assertions():
    with pytest.raises(AssertionError):
        CTypeDataStore(size=3, data_type="I", stride=4, element_count=1)

    store = CTypeDataStore(size=8, data_type="I", stride=4, element_count=1)
    with pytest.raises(AssertionError):
        store.set_bytes(7, b"\x00\x01")


def test_buffer_object_create_resize_and_delete(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLBufferObject(ctx, 16)
    assert buffer.size == 16
    with pytest.raises(AssertionError):
        buffer.get_bytes()

    payload = bytes(range(16))
    buffer.set_bytes(payload)
    assert buffer.get_bytes() == payload

    buffer.set_bytes_region(4, b"\xaa\xbb\xcc\xdd")
    expected = bytearray(payload)
    expected[4:8] = b"\xaa\xbb\xcc\xdd"
    assert buffer.get_bytes() == bytes(expected)

    buffer.resize(24)
    resized = buffer.get_bytes()
    assert buffer.size == 24
    assert resized[:16] == bytes(expected)

    buffer.resize(8)
    assert buffer.get_bytes() == bytes(expected[:8])

    buffer.delete()
    assert buffer.id is None
    buffer.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_index_buffer_creation_vao_element_buffer(gl3_context):
    """This makes sure creating an index buffer does not overwrite the existing VAO's bound index buffer."""
    from pyglet.graphics.api.gl import GL_ELEMENT_ARRAY_BUFFER, GL_ELEMENT_ARRAY_BUFFER_BINDING, GLint, GLuint

    gl3_context.switch_to()
    ctx = gl3_context.context

    vao = GLuint()
    ctx.glGenVertexArrays(1, vao)
    created = None
    anchor = None
    ctx.glBindVertexArray(vao)
    try:
        anchor = GLBufferObject(ctx, 8, target=GL_ELEMENT_ARRAY_BUFFER)
        anchor.set_bytes(b"\x00" * 8)

        bound_before = GLint()
        ctx.glGetIntegerv(GL_ELEMENT_ARRAY_BUFFER_BINDING, bound_before)
        assert bound_before.value == anchor.id

        created = GLIndexedBufferObject(ctx, size=8, data_type="I", stride=4, count=1)
        bound_after = GLint()
        ctx.glGetIntegerv(GL_ELEMENT_ARRAY_BUFFER_BINDING, bound_after)
        assert bound_after.value == anchor.id
    finally:
        if created is not None:
            created.delete()
        if anchor is not None:
            anchor.delete()
        ctx.glBindVertexArray(0)
        ctx.glDeleteVertexArrays(1, vao)


def test_buffer_object_assertions(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context
    buffer = GLBufferObject(ctx, 8)

    with pytest.raises(AssertionError):
        buffer.set_bytes(b"\x00")
    with pytest.raises(AssertionError):
        buffer.get_bytes()
    with pytest.raises(AssertionError):
        buffer.get_bytes_region(-1, 1)
    with pytest.raises(AssertionError):
        buffer.set_bytes_region(7, b"\x00\x01")

    buffer.delete()

@require_graphics_api(GraphicsAPIGroups.GL3)
def test_mapped_buffer_region_updates(gl3_context):
    # Mapped buffers aren't supported by GLES2.
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLMappedBufferObject(ctx, 16)

    whole = buffer.map()
    whole[:] = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
    buffer.unmap()
    assert buffer.get_bytes() == bytes(range(16))

    ptr_type = ctypes.POINTER(ctypes.c_ubyte * 4)
    region = buffer.map_range(6, 4, ptr_type)
    region[:] = (ctypes.c_ubyte * 4)(90, 91, 92, 93)
    buffer.unmap()

    expected = bytearray(range(16))
    expected[6:10] = bytes((90, 91, 92, 93))
    assert buffer.get_bytes() == bytes(expected)

    buffer.delete()
    assert buffer.id is None


def test_backed_index_buffer_commit_resize_and_delete(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLIndexedBufferObject(ctx, size=8, data_type="I", stride=4, count=1)

    buffer.set_region(0, 2, [5, 9])
    buffer.commit()

    cpu_data = buffer.get_bytes()
    gpu_data = GLBufferObject.get_bytes(buffer)
    assert gpu_data == cpu_data

    values = (ctypes.c_uint32 * 2).from_buffer_copy(gpu_data)
    assert tuple(values) == (5, 9)

    buffer.resize(16)
    buffer.set_region(2, 2, [12, 13])
    buffer.commit()

    cpu_data_resized = buffer.get_bytes()
    gpu_data_resized = GLBufferObject.get_bytes(buffer)
    assert gpu_data_resized == cpu_data_resized

    values_resized = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data_resized)
    assert tuple(values_resized[:2]) == (5, 9)
    assert tuple(values_resized[2:4]) == (12, 13)

    buffer.delete()
    assert buffer.id is None
    buffer.delete()


def test_backed_index_buffer_first_partial_commit_allocates_and_uploads(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLIndexedBufferObject(ctx, size=16, data_type="I", stride=4, count=1)

    buffer.set_data_region([7], start=0, length=4)
    buffer.commit()

    gpu_data = GLBufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (7, 0, 0, 0)

    buffer.delete()


def test_backed_index_buffer_set_data_with_ctypes_array(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLIndexedBufferObject(ctx, size=16, data_type="I", stride=4, count=1)

    initial_values = (ctypes.c_uint32 * 4)(11, 22, 33, 44)
    buffer.set_data(initial_values)
    buffer.commit()

    gpu_data = GLBufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (11, 22, 33, 44)

    buffer.delete()


def test_backed_index_buffer_set_data_with_python_list(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLIndexedBufferObject(ctx, size=16, data_type="I", stride=4, count=1)

    buffer.set_data([11, 22, 33, 44])
    buffer.commit()

    gpu_data = GLBufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (11, 22, 33, 44)

    buffer.delete()


def test_backed_index_buffer_set_data_region_with_python_list(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLIndexedBufferObject(ctx, size=16, data_type="I", stride=4, count=1)

    initial_values = (ctypes.c_uint32 * 4)(11, 22, 33, 44)
    buffer.set_data(initial_values)
    buffer.commit()

    buffer.set_data_region([99, 100], start=8, length=8)
    buffer.commit()

    gpu_data = GLBufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (11, 22, 99, 100)

    buffer.delete()


def test_backed_index_buffer_set_data_ptr_with_ctypes_pointer(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLIndexedBufferObject(ctx, size=16, data_type="I", stride=4, count=1)

    initial_values = (ctypes.c_uint32 * 4)(11, 22, 33, 44)
    buffer.set_data(initial_values)
    buffer.commit()

    ptr_values = (ctypes.c_uint32 * 2)(7, 8)
    ptr = ctypes.cast(ptr_values, ctypes.POINTER(ctypes.c_ubyte))
    buffer.set_data_ptr(0, 8, ptr)
    buffer.commit()

    gpu_data = GLBufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (7, 8, 33, 44)

    buffer.delete()

@require_graphics_api(GraphicsAPIGroups.DESKTOP_GL)
def test_gl_vertex_stream_persistent_resize_rebinds_vao(gl3_context):
    from pyglet.graphics.api.gl import GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING, GLint
    from pyglet.graphics.api.gl.buffer import PersistentBufferObject
    from pyglet.graphics.api.gl.vertexdomain import GLVertexArrayBinding, GLVertexStream

    gl3_context.switch_to()
    ctx = gl3_context.context
    info = ctx.get_info()

    if info.get_opengl_api() != "opengl":
        pytest.skip("Persistent buffers are only integrated for desktop OpenGL contexts.")
    if not (info.have_version(4, 4) or info.have_extension("GL_ARB_buffer_storage")):
        pytest.skip("Persistent buffers require OpenGL 4.4 or GL_ARB_buffer_storage.")

    previous_option = pyglet.options.opengl_persistent_buffers
    stream = None
    vao_binding = None
    pyglet.options.opengl_persistent_buffers = True
    try:
        stream = GLVertexStream(ctx, initial_size=2, attrs=[Attribute("position", 0, 2, "f")])
        buffer = stream.buffers[0]
        assert isinstance(buffer, PersistentBufferObject)

        vao_binding = GLVertexArrayBinding(ctx, [stream])

        buffer.set_region(0, 2, [1.0, 2.0, 3.0, 4.0])
        old_id = buffer.id
        stream.resize(4)

        assert buffer.id != old_id
        assert list(buffer.get_region(0, 2)) == [1.0, 2.0, 3.0, 4.0]

        vao_binding.bind()
        bound_buffer = GLint()
        ctx.glGetVertexAttribiv(0, GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING, bound_buffer)
        vao_binding.unbind()
        assert bound_buffer.value == buffer.id
    finally:
        pyglet.options.opengl_persistent_buffers = previous_option
        if vao_binding is not None:
            vao_binding.vao.delete()
        if stream is not None:
            for buf in stream.buffers:
                buf.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_uniform_buffer_reserves_resource_ranges_and_grows(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    program = pyglet.graphics.get_default_shader()
    window_block = program.uniform_blocks["WindowBlock"]

    ubo = window_block.create_ubo(copies_per_resource=2)
    try:
        ranges_a = ubo.reserve_resource_range()
        ranges_b = ubo.reserve_resource_range(copies_per_resource=3)

        assert len(ranges_a) == 2
        assert len(ranges_b) == 3
        assert ctx.info.MAX_UNIFORM_BUFFER_OFFSET_ALIGNMENT > 0
        assert ubo.slice_stride % ctx.info.MAX_UNIFORM_BUFFER_OFFSET_ALIGNMENT == 0

        assert ubo.planned_size >= ubo.slice_stride * 5
        assert ranges_a[0].offset == ubo.slice_stride
        assert ranges_a[1].offset == ubo.slice_stride * 2
        assert ranges_b[0].offset == ubo.slice_stride * 3
        assert ranges_b[2].offset == ubo.slice_stride * 5
    finally:
        ubo.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_uniform_buffer_upload_lazily_reserves_resource_ranges(gl3_context):
    gl3_context.switch_to()

    program = pyglet.graphics.get_default_shader()
    window_block = program.uniform_blocks["WindowBlock"]
    ubo = window_block.create_ubo(copies_per_resource=2)

    try:
        assert len(ubo._ranges) == 0  # noqa: SLF001

        camera_data = ubo.get_data_structure()
        camera_data.view[:] = pyglet.math.Mat4()
        camera_data.projection[:] = pyglet.math.Mat4.orthogonal_projection(0, 1, 0, 1, -1, 1)
        binding = ubo.upload_to_available_binding(camera_data)

        assert len(ubo._ranges) >= 1  # noqa: SLF001
        assert binding.offset == ubo._ranges[0].offset  # noqa: SLF001
        assert binding.size == ubo.slice_size
    finally:
        ubo.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_uniform_buffer_ranges_are_released_by_frame_resources(gl3_context, monkeypatch):
    gl3_context.switch_to()
    ctx = gl3_context.context
    ctx.frame_resources.delete()
    ctx.frame_resources.frame_begin(0)

    fence = object()
    deleted_fences = []
    monkeypatch.setattr(ctx, "create_frame_fence", lambda: fence)
    monkeypatch.setattr(ctx, "poll_frame_fence", lambda submitted_fence: submitted_fence is fence)
    monkeypatch.setattr(ctx, "delete_frame_fence", deleted_fences.append)

    program = pyglet.graphics.get_default_shader()
    window_block = program.uniform_blocks["WindowBlock"]
    ubo = window_block.create_ubo(copies_per_resource=2)

    try:
        camera_data = ubo.get_data_structure()
        binding = ubo.upload_to_available_binding(camera_data)
        range_ = ubo._find_range_for_binding(binding)  # noqa: SLF001

        assert range_.in_use
        assert range_ in ctx.frame_resources.active_slot.ubo_ranges

        assert not ctx.frame_active
        ubo._commit_data(range_, camera_data)  # noqa: SLF001

        ctx.frame_resources.frame_submit()
        assert ctx.frame_resources.active_slot.fence is fence

        ctx.frame_resources.frame_begin(len(ctx.frame_resources.slots))
        assert not range_.in_use
        assert deleted_fences == [fence]
    finally:
        ubo.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_uniform_buffer_range_can_be_modified_outside_active_frame(gl3_context, monkeypatch):
    gl3_context.switch_to()
    ctx = gl3_context.context
    ctx.frame_resources.delete()

    monkeypatch.setattr(ctx, "create_frame_fence", object)
    monkeypatch.setattr(ctx, "poll_frame_fence", lambda _fence: True)
    monkeypatch.setattr(ctx, "delete_frame_fence", lambda _fence: None)

    program = pyglet.graphics.get_default_shader()
    window_block = program.uniform_blocks["WindowBlock"]
    ubo = window_block.create_ubo(copies_per_resource=2)

    try:
        camera_data = ubo.get_data_structure()

        ctx.frame_resources.frame_begin(0)
        binding = ubo.upload_to_available_binding(camera_data)
        range_ = ubo._find_range_for_binding(binding)  # noqa: SLF001
        ctx.frame_resources.frame_submit()

        assert range_.in_use
        assert not ctx.frame_active
        ubo._commit_data(range_, camera_data)  # noqa: SLF001
    finally:
        ubo.delete()
        ctx.frame_resources.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_rebound_uniform_buffer_range_stays_in_use_until_all_frame_slots_release(gl3_context, monkeypatch):
    gl3_context.switch_to()
    ctx = gl3_context.context
    ctx.frame_resources.delete()

    monkeypatch.setattr(ctx, "create_frame_fence", object)
    monkeypatch.setattr(ctx, "poll_frame_fence", lambda _fence: True)
    monkeypatch.setattr(ctx, "delete_frame_fence", lambda _fence: None)

    program = pyglet.graphics.get_default_shader()
    window_block = program.uniform_blocks["WindowBlock"]
    ubo = window_block.create_ubo(copies_per_resource=2)

    try:
        camera_data = ubo.get_data_structure()

        ctx.frame_resources.frame_begin(0)
        binding = ubo.upload_to_available_binding(camera_data)
        range_ = ubo._find_range_for_binding(binding)  # noqa: SLF001
        ctx.frame_resources.frame_submit()

        ctx.frame_resources.frame_begin(1)
        ubo.use_range(range_)
        ctx.frame_resources.frame_submit()

        ctx.frame_resources.frame_begin(2)
        ubo.use_range(range_)
        ctx.frame_resources.frame_submit()

        assert range_.in_use
        assert range_.frame_use_count == 3

        ctx.frame_resources.frame_begin(3)
        assert range_.in_use
        assert range_.frame_use_count == 2
        assert not ctx.frame_active
        ubo._commit_data(range_, camera_data)  # noqa: SLF001

        ctx.frame_resources.frame_begin(4)
        assert range_.in_use
        assert range_.frame_use_count == 1

        ctx.frame_resources.frame_begin(5)
        assert not range_.in_use
        assert range_.frame_use_count == 0
    finally:
        ubo.delete()
        ctx.frame_resources.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_uniform_buffer_bind_slice_uses_slice_offset_and_size(gl3_context):
    from pyglet.graphics.api.gl import gl

    gl3_context.switch_to()
    ctx = gl3_context.context

    program = pyglet.graphics.get_default_shader()
    window_block = program.uniform_blocks["WindowBlock"]
    ubo = window_block.create_ubo(copies_per_resource=2)

    try:
        camera_data = ubo.get_data_structure()
        camera_data.view[:] = pyglet.math.Mat4()
        camera_data.projection[:] = pyglet.math.Mat4.orthogonal_projection(0, 1, 0, 1, -1, 1)
        binding = ubo.upload_to_available_binding(camera_data)

        ubo.bind_slice(binding, binding_index=window_block.binding)

        bound_buffer = gl.GLint()
        start = gl.GLint()
        size = gl.GLint()
        ctx.glGetIntegeri_v(gl.GL_UNIFORM_BUFFER_BINDING, window_block.binding, bound_buffer)
        ctx.glGetIntegeri_v(gl.GL_UNIFORM_BUFFER_START, window_block.binding, start)
        ctx.glGetIntegeri_v(gl.GL_UNIFORM_BUFFER_SIZE, window_block.binding, size)

        assert bound_buffer.value == ubo.id
        assert start.value == binding.offset
        assert size.value == binding.size
    finally:
        ubo.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_uniform_buffer_bound_range_cannot_be_modified(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context
    ctx.frame_resources.delete()
    ctx.frame_begin()

    program = pyglet.graphics.get_default_shader()
    window_block = program.uniform_blocks["WindowBlock"]
    ubo = window_block.create_ubo(copies_per_resource=2)

    try:
        camera_data = ubo.get_data_structure()
        camera_data.view[:] = pyglet.math.Mat4()
        camera_data.projection[:] = pyglet.math.Mat4.orthogonal_projection(0, 1, 0, 1, -1, 1)
        binding = ubo.upload_to_available_binding(camera_data)
        range_ = ubo._find_range_for_binding(binding)  # noqa: SLF001

        ubo.bind_slice(binding, binding_index=window_block.binding)
        ubo.use_range(range_)

        with pytest.raises(RuntimeError, match="Cannot modify a UBO range"):
            ubo._commit_data(range_, camera_data)  # noqa: SLF001
    finally:
        ubo.delete()
        ctx.frame_end()
        ctx.frame_resources.delete()


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_ubo_resource_ranges_stay_valid_across_multiple_resizes(gl3_context):
    from pyglet.graphics.api.gl import gl

    gl3_context.switch_to()
    ctx = gl3_context.context

    program = pyglet.graphics.get_default_shader()
    window_block = program.uniform_blocks["WindowBlock"]
    ubo = window_block.create_ubo(copies_per_resource=2)

    try:
        data_a = ubo.get_data_structure()
        data_a.view[:] = pyglet.math.Mat4()
        data_a.projection[:] = pyglet.math.Mat4.orthogonal_projection(0, 1, 0, 1, -1, 1)
        binding_a = ubo.upload_to_available_binding(data_a)

        data_b = ubo.get_data_structure()
        data_b.view[:] = pyglet.math.Mat4().translate((0.25, 0.0, 0.0))
        data_b.projection[:] = pyglet.math.Mat4.orthogonal_projection(0, 1, 0, 1, -1, 1)
        binding_b = ubo.upload_to_available_binding(data_b)

        before_a = ubo.buffer.get_data_region(binding_a.offset, binding_a.size)
        before_b = ubo.buffer.get_data_region(binding_b.offset, binding_b.size)

        # 2 -> 4 on third allocation, then 4 -> 8 on fifth allocation.
        ubo.reserve_resource_range(copies_per_resource=2)
        ubo.reserve_resource_range(copies_per_resource=2)
        ranges_e = ubo.reserve_resource_range(copies_per_resource=2)

        assert ubo.buffer.get_data_region(binding_a.offset, binding_a.size) == before_a
        assert ubo.buffer.get_data_region(binding_b.offset, binding_b.size) == before_b
        assert ranges_e[0].offset >= binding_b.offset + (ubo.slice_stride * 5)

        ubo.bind_slice(binding_a, binding_index=window_block.binding)
        bound_buffer = gl.GLint()
        start = gl.GLint()
        size = gl.GLint()
        ctx.glGetIntegeri_v(gl.GL_UNIFORM_BUFFER_BINDING, window_block.binding, bound_buffer)
        ctx.glGetIntegeri_v(gl.GL_UNIFORM_BUFFER_START, window_block.binding, start)
        ctx.glGetIntegeri_v(gl.GL_UNIFORM_BUFFER_SIZE, window_block.binding, size)

        assert bound_buffer.value == ubo.id
        assert start.value == binding_a.offset
        assert size.value == binding_a.size

        data_a.view[:] = pyglet.math.Mat4().translate((0.5, 0.0, 0.0))
        binding_a2 = ubo.upload_to_available_binding(data_a)
        after_a2 = ubo.buffer.get_data_region(binding_a2.offset, binding_a2.size)

        if binding_a2.offset == binding_a.offset:
            assert after_a2 != before_a
        assert ubo.buffer.get_data_region(binding_b.offset, binding_b.size) == before_b
    finally:
        ubo.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_ubo_ring_buffer_strict_mode_errors_when_all_ranges_are_in_use(gl3_context):
    gl3_context.switch_to()

    program = pyglet.graphics.get_default_shader()
    window_block = program.uniform_blocks["WindowBlock"]
    ubo = window_block.create_ubo(copies_per_resource=1, strict=True)

    try:
        camera_data = ubo.get_data_structure()
        ubo.upload_to_available_binding(camera_data)

        with pytest.raises(RuntimeError, match="RingBuffer has no writable range"):
            ubo.upload_to_available_binding(camera_data)
    finally:
        ubo.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_ubo_ring_buffer_non_strict_mode_expands_when_all_ranges_are_in_use(gl3_context):
    gl3_context.switch_to()

    program = pyglet.graphics.get_default_shader()
    window_block = program.uniform_blocks["WindowBlock"]
    ubo = window_block.create_ubo(copies_per_resource=1, strict=False)

    try:
        camera_data = ubo.get_data_structure()
        first_binding = ubo.upload_to_available_binding(camera_data)

        range_count_before = len(ubo._ranges)  # noqa: SLF001
        planned_size_before = ubo.planned_size

        second_binding = ubo.upload_to_available_binding(camera_data)

        assert len(ubo._ranges) == range_count_before + 1  # noqa: SLF001
        assert second_binding.offset >= first_binding.offset + ubo.slice_stride
        assert ubo.planned_size >= planned_size_before + ubo.slice_stride
    finally:
        ubo.delete()

