import pyglet
pyglet.options["scale_window_content"] = True
pyglet.options["debug_gl"] = False

window = pyglet.window.Window(800, 600, caption="DPI Test", resizable=True)

image = pyglet.image.load("programming_guide/kitten.jpg")

dinosaur = pyglet.resource.animation("programming_guide/dinosaur.gif")

sprite = pyglet.sprite.Sprite(dinosaur)

@window.event
def on_draw():
    window.clear()
    sprite.draw()
    image.blit(window.width-image.width, window.height-image.height)

@window.event
def on_mouse_press(x, y, button, modifier):
    print("Window Size:", window.get_size())

@window.event
def on_scale(scale_x, scale_y, x_dpi, y_dpi):
    print("SCALE_X", scale_x, scale_y, x_dpi, y_dpi)
    print("Window Size:", window.get_size())
    print("Window Pixel Ratio:", window.get_pixel_ratio())
    print("Window Frame Buffer Size:", window.get_framebuffer_size())

pyglet.app.run()