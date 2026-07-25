import pyglet

window = pyglet.window.Window()
image = pyglet.resource.texture('kitten.jpg')


@window.event
def on_draw():
    window.clear()
    image.blit(0, 0)


pyglet.app.run()
