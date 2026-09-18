"""Resizing from one UI manager through ScrollableRegion and VBox."""

import pyglet


class ResizeAwareButton(pyglet.gui.TextButton):
    def on_resize(self, width: int, height: int) -> None:
        self.text = f"Resized to: {width} x {height}"


window = pyglet.window.Window(640, 360, "Widget Layout Resizing", resizable=True)
batch = pyglet.graphics.Batch()
ui = pyglet.gui.UIManager(window)

region = pyglet.gui.ScrollableRegion(ui, 40, 40, 560, 260, camera=window.camera, batch=batch)
region.set_style(
    pyglet.gui.LayoutCellStyle(
        background=(25, 35, 55, 255),
        padding=(12, 12, 12, 12),
        stretch_content=(True, False),
        content_alignment=("left", "top"),
    ),
)
content = pyglet.gui.VBox(
    region, 40, 40, 560, 500,
    style=pyglet.gui.LayoutStyle(
        background=(40, 55, 80, 255),
        padding=(8, 8, 8, 8),
        cell_background=(55, 75, 105, 255),
        cell_padding=(6, 12, 6, 12),
        cell_margin=(0, 6),
        cell_content_alignment=("center", "center"),
        cell_stretch_content=(True, False),
        row_size=42,
    ),
    batch=batch,
    group=region.content_group,
)
region.content = content

for index in range(10):
    button = ResizeAwareButton(
        region, 0, 0, f"Item {index + 1}", batch=batch, group=region.content_group,
        style=pyglet.gui.TextButtonStyle(
            unpressed_color=(225, 235, 255, 255),
            hover_color=(120, 205, 255, 255),
            pressed_color=(255, 190, 100, 255),
        ),
    )
    content.append(button)


def on_resize(width, height):
    region.position = 40, 40
    region.size = width - 80, height - 100

# Push the resize handlers, as @window.event will replace the event.
window.push_handlers(on_resize=on_resize)


@window.event
def on_draw():
    window.clear()
    batch.draw()


pyglet.app.run()
