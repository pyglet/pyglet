"""Use UI element resizing to scale a button with a window's size.

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
             |       button area        |  |  growth
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

# Add space around the window to make sure button hovering works
PADDING_PX = 30
DOUBLE_PADDING = PADDING_PX * 2


window = pyglet.window.Window(
    500, 500,
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


# Load textures
depressed = pyglet.resource.image('button_up.png')
pressed = pyglet.resource.image('button_down.png')
hover = pyglet.resource.image('button_hover.png')


push_label = pyglet.text.Label(
    "Push Button: False",
    x=0, y=0,
    batch=batch, color=(0, 0, 0, 255)
)
pushbutton = pyglet.gui.PushButton(
    PADDING_PX, PADDING_PX,
    pressed, depressed,
    hover=hover, batch=batch,
    width=window.width - DOUBLE_PADDING, height=window.height - DOUBLE_PADDING
)


# Update the bottom left display label
def update_label_text():
    push_label.text =\
        f"Push Button: pressed={pushbutton.value}, "\
        f"width={pushbutton.width}, height={pushbutton.height}"


# Use a decorator to register the resize handler to make sure
# we scale the drawing area as the window grows and shrinks.
@window.event
def on_resize(width, height):
    pushbutton.size = width - DOUBLE_PADDING, height - DOUBLE_PADDING
    update_label_text()


pushbutton.set_handler('on_press', update_label_text)
pushbutton.set_handler('on_release', update_label_text)
frame.add_widget(pushbutton)


pyglet.app.run()
