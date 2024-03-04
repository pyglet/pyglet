import pyglet
pyglet.options["scale_with_dpi"] = True
pyglet.options["debug_gl"] = False

window = pyglet.window.Window(800, 600, caption="DPI Test", resizable=True)

print(window.dpi, window.scale)

label = pyglet.text.Label('Hello, world',
                          font_name='Times New Roman',
                          font_size=36,
                          x=window.width//2, y=window.height//2,
                          anchor_x='center', anchor_y='center'
                          )

dinosaur = pyglet.resource.animation("programming_guide/dinosaur.gif")

sprite = pyglet.sprite.Sprite(dinosaur, x=100, y=100)

@window.event
def on_draw():
    window.clear()
    sprite.draw()
    label.draw()

@window.event
def on_mouse_press(x, y, button, modifier):
    print("Window Size:", window.get_size())
    print("Scaled Click:", x, y)

@window.event
def on_resize(width, height):
    window.on_resize(width, height)
    print("RESIZED", width, height)

@window.event
def on_scale(scale, dpi):
    print("SCALE_X", scale, dpi)
    print("Window Size:", window.get_size())
    print("Window Pixel Ratio:", window.get_pixel_ratio())
    print("Window Frame Buffer Size:", window.get_framebuffer_size())

pyglet.app.run()
