from __future__ import annotations

import pyglet
from pyglet.enums import GeometryMode
from pyglet.graphics.api.gl import GL_ELEMENT_ARRAY_BUFFER_BINDING, GLint

from tests.annotations import GraphicsAPI, require_graphics_api


def _create_quad_vertices(x: float, y: float, z: float, width: float, height: float) -> tuple[float, ...]:
    return (
        x, y, z,
        x + width, y, z,
        x + width, y + height, z,
        x, y + height, z,
    )


@require_graphics_api(GraphicsAPI.GL2)
def test_gl2_indexed_batch_draw_keeps_element_buffer_bound(gl3_context) -> None:
    """Ensure GL2 indexed draws bind EBO every draw, even when index buffer is not dirty."""
    gl3_context.switch_to()
    ctx = gl3_context.context
    program = pyglet.graphics.api.get_default_shader()
    batch = pyglet.graphics.Batch()

    vertices = _create_quad_vertices(0, 0, 0, 50, 50)
    colors = (1, 0.5, 0.2, 1) * 4
    indices = [0, 1, 2, 0, 2, 3]

    program.vertex_list_indexed(
        4,
        GeometryMode.TRIANGLES,
        indices,
        batch=batch,
        group=None,
        position=("f", vertices),
        colors=("f", colors),
    )

    original_draw_elements = ctx.glDrawElements
    original_multi_draw_elements = ctx.glMultiDrawElements
    observed_bindings: list[int] = []

    def checked_draw_elements(mode, count, gl_type, offset):  # noqa: ANN001
        binding = GLint()
        ctx.glGetIntegerv(GL_ELEMENT_ARRAY_BUFFER_BINDING, binding)
        observed_bindings.append(binding.value)
        assert binding.value != 0, "GL_ELEMENT_ARRAY_BUFFER was not bound during glDrawElements."
        return original_draw_elements(mode, count, gl_type, offset)

    def checked_multi_draw_elements(mode, counts, gl_type, offsets, primcount):  # noqa: ANN001
        binding = GLint()
        ctx.glGetIntegerv(GL_ELEMENT_ARRAY_BUFFER_BINDING, binding)
        observed_bindings.append(binding.value)
        assert binding.value != 0, "GL_ELEMENT_ARRAY_BUFFER was not bound during glMultiDrawElements."
        return original_multi_draw_elements(mode, counts, gl_type, offsets, primcount)

    ctx.glDrawElements = checked_draw_elements
    ctx.glMultiDrawElements = checked_multi_draw_elements
    try:
        # First draw commits new buffers. Second draw is the regression case: no dirty index data.
        batch.draw()
        batch.draw()
    finally:
        ctx.glDrawElements = original_draw_elements
        ctx.glMultiDrawElements = original_multi_draw_elements

    assert len(observed_bindings) >= 2
