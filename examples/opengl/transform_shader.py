"""Capture position and lifetime using Group/State transform feedback.

Run with --interleaved to pack both outputs into one buffer; the default uses
separate buffers in varying order.

This example shows how to:
1. Create a TransformFeedbackShaderProgram.
2. Capture vertex shader outputs into a transform feedback buffer.
3. Read back and print the captured data.

Press SPACE to run another capture pass.
Press R to reset to the initial positions.
"""
from __future__ import annotations

import sys
from typing import Sequence, TYPE_CHECKING

import pyglet
from pyglet.enums import GeometryMode
from pyglet.graphics import Group, Shader, ShaderGroup, State, TransformFeedbackShaderProgram
from pyglet.graphics.api.gl import (
    GL_POINTS, GL_PROGRAM_POINT_SIZE, GL_RASTERIZER_DISCARD, GL_TRANSFORM_FEEDBACK_BUFFER,
)
from pyglet.graphics.api.gl.buffer import GLTransformFeedbackBufferObject

if TYPE_CHECKING:
    from pyglet.graphics.draw import DrawContext


window = pyglet.window.Window(960, 540, "Transform Feedback Example")
packing = "interleaved" if "--interleaved" in sys.argv else "separate"
label = pyglet.text.Label(f"{packing}: SPACE to advance, R to reset", x=10, y=10)

vertex_source = """#version 330 core
    in vec2 position;
    in float lifetime;
    out vec2 feedback_position;
    out float feedback_lifetime;

    uniform vec2 displacement;
    uniform float elapsed;

    void main()
    {
        feedback_position = position + displacement;
        feedback_lifetime = max(0.0, lifetime - elapsed);
        gl_Position = vec4(feedback_position, 0.0, 1.0);
        gl_PointSize = 8.0 + 8.0 * feedback_lifetime;
    }
"""
fragment_source = """#version 330 core
    in float feedback_lifetime;
    out vec4 final_colors;

    void main()
    {
        final_colors = vec4(0.95, 0.2 + 0.6 * feedback_lifetime, 0.35, 1.0);
    }
"""
vertex_shader = Shader(vertex_source, "vertex")
fragment_shader = Shader(fragment_source, "fragment")
program = TransformFeedbackShaderProgram(
    vertex_shader, fragment_shader,
    varyings=("feedback_position", "feedback_lifetime"),
    varying_buffer_type=packing,
    vertex_layout=None,
)

initial_positions = (-0.65, -0.35, -0.15, 0.15, 0.25, -0.10, 0.60, 0.40)
initial_lifetimes = (1.0, 0.8, 0.6, 0.4)
particle_count = len(initial_lifetimes)
current_positions = list(initial_positions)
current_lifetimes = list(initial_lifetimes)
step_count = 0
context = window.context
context.glEnable(GL_PROGRAM_POINT_SIZE)

# Interleaved: [x, y, lifetime] per particle, one binding.
# Separate: [x, y] in binding 0, [lifetime] in binding 1.
buffer_sizes = (particle_count * 12,) if packing == "interleaved" else (particle_count * 8, particle_count * 4)
feedback_buffers = tuple(GLTransformFeedbackBufferObject(context, size, data_type="f") for size in buffer_sizes)


class TransformFeedbackState(State):
    """Begin/end point capture around the child group's draws."""

    sets_state: bool = True
    unsets_state: bool = True
    group_hash: bool = False
    _buffers: tuple[GLTransformFeedbackBufferObject, ...]

    def __init__(self, buffers: tuple[GLTransformFeedbackBufferObject, ...]) -> None:
        self._buffers = buffers

    def set_state(self, ctx: DrawContext) -> None:
        for index, buffer in enumerate(self._buffers):
            buffer.bind_base(index)
        ctx.surface_ctx.glEnable(GL_RASTERIZER_DISCARD)
        ctx.surface_ctx.glBeginTransformFeedback(GL_POINTS)

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.glEndTransformFeedback()
        ctx.surface_ctx.glDisable(GL_RASTERIZER_DISCARD)
        for index in range(len(self._buffers)):
            ctx.surface_ctx.glBindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER, index, 0)


# Bind the shader before beginning feedback; each vertex-list group supplies its program.
capture_group = Group()
capture_group.set_shader_program(program)
capture_group.set_state(TransformFeedbackState(feedback_buffers))
render_group = ShaderGroup(program)
capture_vertex_list = program.vertex_list(
    particle_count, GeometryMode.POINTS, group=capture_group,
    position=current_positions, lifetime=current_lifetimes,
)
render_vertex_list = program.vertex_list(
    particle_count, GeometryMode.POINTS, group=render_group,
    position=current_positions, lifetime=current_lifetimes,
)


def run_transform_feedback(dx: float = 0.12, dy: float = 0.05,
                           elapsed: float = 0.1) -> tuple[list[float], list[float]]:
    program["displacement"] = (dx, dy)
    program["elapsed"] = elapsed
    capture_vertex_list.draw(GeometryMode.POINTS)
    if packing == "interleaved":
        records = feedback_buffers[0].get_data()[:]
        positions = [records[i + component] for i in range(0, len(records), 3) for component in (0, 1)]
        lifetimes = records[2::3]
    else:
        positions = feedback_buffers[0].get_data()[:]
        lifetimes = feedback_buffers[1].get_data()[:]
    return positions, lifetimes


def apply_state(positions: Sequence[float], lifetimes: Sequence[float]) -> None:
    current_positions[:] = positions
    current_lifetimes[:] = lifetimes
    for vertices in (capture_vertex_list, render_vertex_list):
        vertices.position[:] = positions
        vertices.lifetime[:] = lifetimes


def print_capture(positions: Sequence[float], lifetimes: Sequence[float]) -> None:
    print(f"Captured {packing} outputs:")
    for index, (x, y, lifetime) in enumerate(zip(positions[0::2], positions[1::2], lifetimes)):
        print(f"  {index}: position=({x:.3f}, {y:.3f}), lifetime={lifetime:.3f}")


@window.event
def on_draw() -> None:
    window.clear()
    program["displacement"] = (0.0, 0.0)
    program["elapsed"] = 0.0
    render_vertex_list.draw(GeometryMode.POINTS)
    label.text = f"{packing}: SPACE to advance, R to reset, steps: {step_count}"
    label.draw()


@window.event
def on_key_press(symbol: int, modifiers: int) -> None:
    global step_count
    if symbol == pyglet.window.key.SPACE:
        positions, lifetimes = run_transform_feedback()
        apply_state(positions, lifetimes)
        step_count += 1
        print_capture(positions, lifetimes)
    elif symbol == pyglet.window.key.R:
        step_count = 0
        apply_state(initial_positions, initial_lifetimes)
        print("Reset to initial positions and lifetimes.")


if __name__ == "__main__":
    positions, lifetimes = run_transform_feedback()
    apply_state(positions, lifetimes)
    step_count = 1
    print_capture(positions, lifetimes)
    pyglet.app.run()
