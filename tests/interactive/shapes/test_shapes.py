import itertools
import inspect
from typing import Dict, Optional, Generator, Tuple, Type

import pyglet.window
import math
from pyglet.shapes import (
    Arc,
    BezierCurve,
    Circle,
    Ellipse,
    Sector,
    Line,
    MultiLine,
    Rectangle,
    BorderedRectangle,
    Triangle,
    Star,
    Polygon,
    Box,
    ShapeBase
)
from pyglet.text import Label

INSTRUCTIONS = """- / = keys to rotate
Arrow keys to change anchor points
Left click + drag to adjust positions
"""

PX_SIZE = 10
PX_SIZE_2 = PX_SIZE * 2

# Call next() to get a new color; endlessly repeats
colors = itertools.cycle(map(lambda c: c + (255,), [
    (255, 0, 0),  # Red
    (0, 255, 0),  # Blue
    (0, 0, 255),  # Green
    (255, 255, 0)  # Yellow
]))

# Default values for each shape type: Type, *args, **kwargs
shape_configs = [
    (Arc, (PX_SIZE,), {}),
    (BezierCurve, [(0, 0), (PX_SIZE, PX_SIZE_2), (PX_SIZE_2, PX_SIZE)], {}),
    (Circle, (PX_SIZE,), {}),
    (Ellipse, (PX_SIZE, PX_SIZE_2,), {}),

    (Sector, (PX_SIZE,), {}),
    (Line, (0, 0, PX_SIZE_2, PX_SIZE_2), {}),
    (Rectangle, (PX_SIZE, PX_SIZE_2), {}),
    (BorderedRectangle, (PX_SIZE_2, PX_SIZE), {}),
    (Box, (PX_SIZE_2, PX_SIZE_2), {}),

    (Triangle, (-PX_SIZE, 0, 0, PX_SIZE, PX_SIZE, 0), {}),
    (Star, (PX_SIZE_2, PX_SIZE, 5), {}),
    (Polygon, ((-PX_SIZE, 0), (0, PX_SIZE), (PX_SIZE, 0)), {}),
    (MultiLine, ((-PX_SIZE, 0), (0, PX_SIZE), (PX_SIZE, 0)), {}),
]


def layout_points(
        width: int, height: int,
        padding: int,
        num_cols: int,
        num_rows: Optional[int] = None
) -> Generator[Tuple[int, int], None, None]:
    """Yield points out in a col / row grid.

    All units in px.
    Args:
        width: Width of the area
        height: Height of the area
        padding: How many px to pad on all sides
        num_cols: How many columns each row should have
        num_rows: Specify to prevent auto-calculation

    Yields:
        Bottom left screen position of the grid cell in px
    """
    x_step_range = width - 2 * padding
    y_step_range = height - 2 * padding

    if num_rows is None:
        num_rows = math.ceil(len(shape_configs) / num_cols)

    x_step = x_step_range // num_cols
    y_step = y_step_range // num_rows

    for y in range(height - padding, y_step, -y_step):
        for x in range(padding, padding + x_step_range, x_step):
            yield x, y


def main():
    padding = 50
    width, height = 600, 600

    window = pyglet.window.Window(
        width, height,
        caption="Shape Translation / Rotation Spotcheck",
        resizable=True)

    shapes: Dict[Type, ShapeBase] = {}
    labels: Dict[Type, Label] = {}
    batch = pyglet.graphics.Batch()

    for shape_config, position in zip(shape_configs, layout_points(window.width, window.height, padding, 4)):
        shape_type, args, kwargs = shape_config
        sig = inspect.signature(shape_type)
        params = list(sig.parameters)
        print(shape_type.__name__, params)

        # Arrange shape args
        if params[:2] == ['x', 'y'] and params[2] != 'x2':
            final_args = position + args
        elif shape_type in (Polygon, BezierCurve, MultiLine):
            raw = [(position[0] + p[0], position[1] + p[1]) for p in args]
            final_args = raw
            print(shape_type.__name__, final_args)

        elif shape_type in (Line, Triangle):
            final_args = [
                position[0] + args[0], position[1] + args[1],
                position[0] + args[2], position[1] + args[3]]
            if shape_type is Triangle:
                final_args += [position[0] + args[4], position[1] + args[5]]
            print(shape_type.__name__, final_args)

        else:
            raise TypeError("unhandled")

        final_kwargs = dict(color=next(colors))
        final_kwargs.update(kwargs)

        label = pyglet.text.Label(
            shape_type.__name__,
            x=position[0], y=position[1] - padding,
            batch=batch,
            anchor_x='center',
            **final_kwargs
        )
        shape = shape_type(*final_args, batch=batch, **final_kwargs)
        shapes[shape_type] = shape
        labels[shape_type] = label

    _instructions = pyglet.text.Label(
        INSTRUCTIONS,
        x=window.width // 2, y=padding,
        width=window.width,
        anchor_x='center',
        align='center',
        batch=batch,
        multiline=True
    )

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    @window.event
    def on_key_press(symbol, modifiers):
        if symbol == pyglet.window.key.MINUS:
            for item in shapes.values():
                item.rotation -= 20
        elif symbol == pyglet.window.key.EQUAL:
            for item in shapes.values():
                item.rotation += 20
        elif symbol == pyglet.window.key.LEFT:
            for item in shapes.values():
                item.anchor_x += 10
        elif symbol == pyglet.window.key.RIGHT:
            for item in shapes.values():
                item.anchor_x -= 10
        elif symbol == pyglet.window.key.DOWN:
            for item in shapes.values():
                item.anchor_y += 10
        elif symbol == pyglet.window.key.UP:
            for item in shapes.values():
                item.anchor_y -= 10

    @window.event
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        if buttons == pyglet.window.mouse.LEFT:
            for item in itertools.chain(shapes.values(), labels.values()):
                item_x, item_y, *item_z = item.position
                item.position = item_x + dx, item_y + dy, *item_z

    # This line is crucial for 2.1 / the development branch
    pyglet.clock.schedule_interval(window.draw, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
