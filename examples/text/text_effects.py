"""An example showing the three main built in text effects: gradients, strokes, and shadows."""

import pyglet
from pyglet.text import DropShadow, LinearGradient, Stroke


window = pyglet.window.Window(960, 700, "Example Text Effects")
window.context.set_clear_color(0.16, 0.18, 0.26, 1.0)

batch = pyglet.graphics.Batch()

labels = [
    # Gradient.
    pyglet.text.Label(
        "Linear gradient fill",
        font_size=38,
        x=window.width // 2,
        y=590,
        anchor_x="center",
        anchor_y="center",
        # Pink to Blue
        color=LinearGradient((255, 90, 140, 255), (80, 185, 255, 255)),
        batch=batch,
    ),
    # Drop shadow.
    pyglet.text.Label(
        "Drop shadow",
        font_size=38,
        x=window.width // 2,
        y=80,
        anchor_x="center",
        anchor_y="center",
        color=(245, 245, 250, 255),
        shadow=DropShadow(offset=(5, -5), color=(20, 25, 45, 210)),
        batch=batch,
    ),
    # Using WAVE makes the differences easier to see.
    pyglet.text.Label(
        "Miter Stroke: WAVE",
        font_size=42,
        x=window.width // 2,
        y=460,
        anchor_x="center",
        anchor_y="center",
        color=(245, 245, 250, 255),
        stroke=Stroke(6, (45, 105, 235, 255), join="miter"),
        batch=batch,
    ),
    pyglet.text.Label(
        "Round Stroke: WAVE",
        font_size=42,
        x=window.width // 2,
        y=330,
        anchor_x="center",
        anchor_y="center",
        color=(245, 245, 250, 255),
        stroke=Stroke(6, (230, 80, 165, 255), join="round"),
        batch=batch,
    ),
    pyglet.text.Label(
        "Bevel Stroke: WAVE",
        font_size=42,
        x=window.width // 2,
        y=200,
        anchor_x="center",
        anchor_y="center",
        color=(245, 245, 250, 255),
        stroke=Stroke(6, (70, 200, 155, 255), join="bevel"),
        batch=batch,
    ),
]


@window.event
def on_draw() -> None:
    window.clear()
    batch.draw()


pyglet.app.run()
