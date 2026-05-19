"""Transform Feedback ShaderProgram example.

This example shows how to:
1. Create a TransformFeedbackShaderProgram.
2. Capture vertex shader outputs into a transform feedback buffer.
3. Read back and print the captured data.

Press SPACE to run another capture pass.
Press R to reset to the initial positions.
"""

from __future__ import annotations

import pyglet

from pyglet.enums import GeometryMode
from pyglet.graphics import Group, Shader, State, TransformFeedbackShaderProgram
from pyglet.graphics.api.gl import GL_DYNAMIC_DRAW, GL_POINTS, GL_PROGRAM_POINT_SIZE, GL_RASTERIZER_DISCARD, \
    OpenGLSurfaceContext
from pyglet.graphics.api.gl.buffer import GLTransformFeedbackBufferObject


window = pyglet.window.Window(960, 540, "Transform Feedback Example")
label = pyglet.text.Label(
    "SPACE: advance feedback, R: reset",
    x=10,
    y=10,
)


vertex_source = """#version 330 core
    in vec2 position;
    out vec2 feedback_position;

    uniform float dx;
    uniform float dy;

    void main()
    {
        vec2 moved = position + vec2(dx, dy);
        feedback_position = moved;
        gl_Position = vec4(moved, 0.0, 1.0);
        gl_PointSize = 12.0;
    }
"""

fragment_source = """#version 330 core
    out vec4 final_colors;

    void main()
    {
        final_colors = vec4(0.95, 0.45, 0.35, 1.0);
    }
"""

vertex_shader = Shader(vertex_source, "vertex")
fragment_shader = Shader(fragment_source, "fragment")

program = TransformFeedbackShaderProgram(
    vertex_shader,
    fragment_shader,
    varyings=("feedback_position",),
    varying_buffer_type="interleaved",
)

initial_positions = (
    -0.65, -0.35,
    -0.15,  0.15,
     0.25, -0.10,
     0.60,  0.40,
)
current_positions = list(initial_positions)
step_count = 0

ctx = pyglet.graphics.api.core.current_context
ctx.glEnable(GL_PROGRAM_POINT_SIZE)
feedback_buffer_size = len(initial_positions) * 4  # 8 floats, 4 bytes each
feedback_buffer = GLTransformFeedbackBufferObject(ctx, feedback_buffer_size,
                                                  usage=GL_DYNAMIC_DRAW,
                                                  data_type="f")


class TransformFeedbackCaptureState(State):
    """State that wraps a draw in a transform feedback capture scope."""
    sets_state: bool = True
    unsets_state: bool = True
    group_hash: bool = False

    def __init__(self, tf_buffer: GLTransformFeedbackBufferObject, binding_index: int = 0) -> None:
        self._buffer = tf_buffer
        self._binding_index = binding_index

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        self._buffer.bind_base(self._binding_index)
        ctx.glEnable(GL_RASTERIZER_DISCARD)
        ctx.glBeginTransformFeedback(GL_POINTS)

    def unset_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.glEndTransformFeedback()
        ctx.glDisable(GL_RASTERIZER_DISCARD)


class TransformFeedbackCaptureGroup(Group):
    def __init__(self, tf_buffer: GLTransformFeedbackBufferObject, order: int = 0, parent: Group | None = None) -> None:
        super().__init__(order=order, parent=parent)
        self.set_state(TransformFeedbackCaptureState(tf_buffer))


capture_group = TransformFeedbackCaptureGroup(feedback_buffer)
render_group = Group()

capture_vertex_list = program.vertex_list(
    4,
    mode=GeometryMode.POINTS,
    group=capture_group,
    position=("f", current_positions),
)

render_vertex_list = program.vertex_list(
    4,
    mode=GeometryMode.POINTS,
    group=render_group,
    position=("f", current_positions),
)


def run_transform_feedback(dx: float = 0.12, dy: float = 0.05) -> list:
    # Feed back previous output as the next input.
    capture_vertex_list.position[:] = current_positions

    program.use()
    program["dx"] = dx
    program["dy"] = dy

    capture_vertex_list.draw(GeometryMode.POINTS)
    program.stop()
    return feedback_buffer.get_data()[:]


def print_capture(data: tuple[float, ...]) -> None:
    pairs = list(zip(data[0::2], data[1::2]))
    print("Captured positions:")
    for i, (x_pos, y_pos) in enumerate(pairs):
        print(f"  {i}: ({x_pos:.3f}, {y_pos:.3f})")


def apply_positions(data: tuple[float, ...]) -> None:
    current_positions[:] = data
    capture_vertex_list.position[:] = data
    render_vertex_list.position[:] = data


def reset_positions() -> None:
    current_positions[:] = initial_positions
    capture_vertex_list.position[:] = initial_positions
    render_vertex_list.position[:] = initial_positions


@window.event
def on_draw() -> None:
    window.clear()

    # Draw original points so there is visible output in the window.
    program.use()
    program["dx"] = 0.0
    program["dy"] = 0.0
    render_vertex_list.draw(GeometryMode.POINTS)
    program.stop()

    label.text = f"SPACE: advance feedback, R: reset, steps: {step_count}"
    label.draw()


@window.event
def on_key_press(symbol: int, modifiers: int) -> None:  # noqa: ARG001
    global step_count
    if symbol == pyglet.window.key.SPACE:
        captured = run_transform_feedback()
        apply_positions(captured)
        step_count += 1
        print_capture(captured)
    elif symbol == pyglet.window.key.R:
        step_count = 0
        reset_positions()
        print("Reset to initial positions.")


if __name__ == "__main__":
    captured = run_transform_feedback()
    apply_positions(captured)
    step_count = 1
    print_capture(captured)
    pyglet.app.run()
