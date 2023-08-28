"""Use UI element resizing to scale sliders with a Window's size

When overriding the Window.on_resize event handler, it is easiest to do
one of the following:

1. Use ``@window.event`` to register an event handler
2. Inherit from the base Window class and call `super().on_resize()`
   at the top of the overriding on_resize method.

This example takes the first approach.

If you do neither, you must manually update the projection, or else
drawing will cut off all drawing above and to the right of the window's
original size:

             +--------------------------+
             |       Window Title       |
             +--------------------------+  ^
             |    + - - - - - - - -+    |  |
             |    |    Cut off     |    |  |  Window
             |           area      |    |  |  growth
         --- +----------------+    |    | ---
          |  |    |  Visible  |         |
 Original |  |    |   area    |    |    |
  height  |  |    +-----------| - -+    |
          |  |                |         |
         --- +----------------+---------+
             |----------------|---------->
                  Original       Window
                   width         growth
"""
import pyglet

SIZE_PX = 250
HALF_SIZE_PX = SIZE_PX // 2

window = pyglet.window.Window(
    SIZE_PX, SIZE_PX,
    caption="Resizable Full-Window Button",
    resizable=True  # Important: make the window resizable
)
batch = pyglet.graphics.Batch()
pyglet.gl.glClearColor(0.8, 0.8, 0.8, 1.0)
frame = pyglet.gui.Frame(window, order=4)


@window.event
def on_draw():
    window.clear()
    batch.draw()


####################################
# Load resources to use for Widgets:
####################################

knob = pyglet.resource.image('knob.png')
thin_bar = pyglet.resource.image('bar.png')
thick_bar = pyglet.resource.image('thick_bar.png')


##########################
# Layout & update helpers:
##########################

# call next() on this to get the next row's y position
row_y_iterator = (SIZE_PX - i * 50 for i in range(1, 5))
original_positions = []
original_sizes = []  # None rows will be skipped when rescaling
items = []


# Add items to
def register_item(item):
    original_positions.append(item.position)
    original_sizes.append(getattr(item, 'size', None))
    items.append(item)


#################################
# Create a thin slider and label:
#################################

thin_label = pyglet.text.Label(
    'Thin Value:   0.0',
    x=HALF_SIZE_PX, y=next(row_y_iterator),
    anchor_x='center',
    anchor_y='center',
    batch=batch, color=(0, 0, 0, 255)
)
register_item(thin_label)


def thin_slider_handler(value):
    thin_label.text = f"Thin Value: {round(value, 1):>5}"


thin_slider = pyglet.gui.Slider(
    (window.width - thin_bar.width) // 2, next(row_y_iterator),
    thin_bar, knob,
    edge=5,
    batch=batch
)
thin_slider.set_handler('on_change', thin_slider_handler)
register_item(thin_slider)
frame.add_widget(thin_slider)


##################################
# Create a thick slider and label:
##################################

thick_label = pyglet.text.Label(
    'Thick Value:   0.0',
    x=HALF_SIZE_PX, y=next(row_y_iterator),
    anchor_y='center',
    anchor_x='center',
    batch=batch, color=(0, 0, 0, 255))
register_item(thick_label)


def thick_slider_handler(value):
    thick_label.text = f"Thick Value: {round(value, 1):>5}"


thick_slider = pyglet.gui.Slider(
    (window.width - thick_bar.width) // 2, next(row_y_iterator),
    thick_bar, knob,
    edge=4,
    batch=batch
)
thick_slider.set_handler('on_change', thick_slider_handler)
register_item(thick_slider)
frame.add_widget(thick_slider)


def scale(value, ratios):
    """Use a tuple of floats to scale x & y values.

    Any remaining coordinates (z) will be appended as-is.
    """
    return value[0] * ratios[0], value[1] * ratios[1], *value[2:]


def rescale_items(scale_ratios):
    for item, position, size in zip(items, original_positions, original_sizes):
        if size is not None:
           item.size = scale(size, scale_ratios)
        item.position = scale(position, scale_ratios)


# Use a decorator to register the resize handler to make sure
# we scale the drawing area as the window grows and shrinks.
@window.event
def on_resize(width, height):
    rescale_items((width / SIZE_PX, height / SIZE_PX))


pyglet.app.run()
