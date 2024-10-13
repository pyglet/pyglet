import pyglet

pyglet.options["debug_gl"] = False
pyglet.options.dpi_scaling = "scaled"

window = pyglet.window.Window(800, 600, caption="DPI Test", resizable=True)
batch = pyglet.graphics.Batch()

print("Window DPI", window.dpi, "Window Scale", window.scale)

hello_label = pyglet.text.Label('Hello, world',
                                font_name='Times New Roman',
                                font_size=36,
                                x=window.width // 2, y=window.height // 2,
                                anchor_x='center', anchor_y='center',
                                batch=batch,
                                dpi=window.dpi)

mouse_enter_label = pyglet.text.Label(f"enter: x={0}, y={0}", x=10, y=110, font_size=12,
                                      dpi=window.dpi, batch=batch)
mouse_leave_label = pyglet.text.Label(f"leave: x={0}, y={0}", x=10, y=85, font_size=12,
                                      dpi=window.dpi, batch=batch)
mouse_motion_label = pyglet.text.Label(f"motion: x={0}, y={0} dx={0}, dy={0}", x=10, y=60, font_size=12,
                                       dpi=window.dpi, batch=batch)
mouse_drag_label = pyglet.text.Label(f"drag: x={0}, y={0} dx={0}, dy={0}", x=10, y=35, font_size=12,
                                     dpi=window.dpi, batch=batch)
mouse_press_label = pyglet.text.Label(f"press: x={0}, y={0}", x=10, y=10, font_size=12,
                                      dpi=window.dpi, batch=batch)
labels = [hello_label, mouse_enter_label, mouse_leave_label, mouse_motion_label, mouse_drag_label, mouse_press_label]

dinosaur = pyglet.resource.animation("programming_guide/dinosaur.gif")

sprite = pyglet.sprite.Sprite(dinosaur, x=100, y=140, batch=batch)
if pyglet.options.dpi_scaling != "real":
    sprite.scale = window.scale


@window.event
def on_draw():
    window.clear()
    batch.draw()


@window.event
def on_mouse_motion(x, y, dx, dy):
    mouse_motion_label.text = f"motion: x={x:.2f}, y={y:.2f} dx={dx:.2f}, dy={dy:.2f}"


@window.event
def on_mouse_press(x, y, button, modifier):
    mouse_press_label.text = f"press: x={x:.2f}, y={y:.2f}"


@window.event
def on_mouse_enter(x, y):
    mouse_enter_label.text = f"enter: x={x:.2f}, y={y:.2f}"


@window.event
def on_mouse_leave(x, y):
    mouse_leave_label.text = f"leave: x={x:.2f}, y={y:.2f}"


@window.event
def on_mouse_drag(x, y, dx, dy, button, modifier):
    mouse_drag_label.text = f"drag: x={x:.2f}, y={y:.2f} dx={dx:.2f}, dy={dy:.2f}"


@window.event
def on_resize(width, height):
    hello_label.position = (window.width // 2, window.height // 2, 0)


screens = pyglet.display.get_display().get_screens()
selected_screen = screens[0]

@window.event
def on_key_press(symbol, modifiers):
    global selected_screen
    if len(screens) > 1:
        if symbol == pyglet.window.key._1:
            selected_screen = screens[1]
        elif symbol == pyglet.window.key._0:
            selected_screen = screens[0]
    
    if symbol == pyglet.window.key.SPACE:
        window.set_size(500, 300)
    elif symbol == pyglet.window.key.F:
        window.set_fullscreen(False, screen=selected_screen)
    elif symbol == pyglet.window.key.G:
        window.set_fullscreen(True, screen=selected_screen)
        


@window.event
def on_scale(scale, dpi):
    print("--- on scale")
    print("SCALE_X", scale, dpi)
    print("Window Size:", window.get_size())
    print("Window Scale Ratio:", window.scale)
    print("Window Frame Buffer Size:", window.get_framebuffer_size())
    if pyglet.options.dpi_scaling != "real":
        for label in labels:
            label.dpi = dpi
        sprite.scale = window.scale


pyglet.app.run()
