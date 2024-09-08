import pyglet

pyglet.options["debug_gl"] = False
pyglet.options.dpi_scaling = "window_and_content"
#pyglet.options.dpi_scaling = False
#pyglet.options.dpi_scaling = "window_only"

# DPI_SCALING
# `False` = 1:1 pixel ratio for Window frame size and framebuffer.
# Note: In MacOS, this is not allowed as the frame size is tied to the resolution, and the resolution determines the DPI.
# As such, to allow 1:1 frame to buffer, it must be in a non-HiDPI resolution.
# However, you can expect the full framebuffer.
#
# `'window_only'` = Window is scaled based on the DPI ratio. Window size and content (projection) size matches the full frame buffer. 
# You must rescale and reposition your content to take advantage of the larger framebuffer. 
# Ex: 800x600 will scale itself based on the DPI. So 1.5 scale would be 1200x900 for `window.get_size` and `window.get_framebuffer_size()`
#
# `'window_and_content'` = Window is scaled based on the DPI ratio. Content size matches original requested size of the window, and is stretched to fit the full framebuffer.
# No rescaling and repositioning of content necessary, but will be blurry.
# Ex: 800x600 will scale itself based on the DPI. 800x600 for `window.get_size()` and 1200x900 for `window.get_framebuffer_size()` at 1.5 scale

window = pyglet.window.Window(800, 600, caption="DPI Test", resizable=True)

print("Window DPI", window.dpi, "Window Scale", window.scale)

label = pyglet.text.Label('Hello, world',
                          font_name='Times New Roman',
                          font_size=36,
                          x=window.width//2, y=window.height//2,
                          anchor_x='center', anchor_y='center',
                          )

dinosaur = pyglet.resource.animation("programming_guide/dinosaur.gif")

sprite = pyglet.sprite.Sprite(dinosaur, x=100, y=100)

@window.event
def on_draw():
    window.clear()
    sprite.draw()
    label.draw()

#@window.event
#def on_mouse_motion(x, y, dx, dy):
#    print("Mouse Motion", x, y, dx, dy)

@window.event
def on_mouse_press(x, y, button, modifier):
    print("Window Size:", window.get_size())
    print("Scaled Click:", x, y)

@window.event
def on_resize(width, height):
    #window.on_resize(width, height)
    print("RESIZED", width, height, window.width, window.height)
    label.position = (window.width // 2, window.height // 2, 0)

@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.SPACE:
        window.set_size(500, 300)

@window.event
def on_scale(scale, dpi):
    print("--- on scale")
    print("SCALE_X", scale, dpi)
    print("Window Size:", window.get_size())
    print("Window Scale Ratio:", window.scale)
    print("Window Frame Buffer Size:", window.get_framebuffer_size())
    #label.dpi = dpi


pyglet.app.run()
