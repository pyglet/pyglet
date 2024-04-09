import pyglet
import random


WIDTH = 1280
HEIGHT = 720
TARGET_FPS = 60

window = pyglet.window.Window(WIDTH, HEIGHT, caption="Benchmark", resizable=True, vsync=False)
label = pyglet.text.Label(" ", x=5, y=5, color=(223, 223, 223, 255), dpi=80)
batch = pyglet.graphics.Batch()


grey_img = pyglet.image.SolidColorImagePattern((50, 50, 50, 150)).create_image(5, 5)
blocks = []


@window.event
def on_draw():
    window.clear()
    batch.draw()
    label.draw()


@window.event
def on_resize(width, height):
    global WIDTH, HEIGHT
    WIDTH, HEIGHT = width, height


def update(dt):

    fps = 1 / dt
    count = int(fps - TARGET_FPS)

    if count > 0:
        for i in range(count//2):
            x = random.uniform(0, WIDTH/2)
            y = random.uniform(0, HEIGHT)
            blocks.append(pyglet.sprite.Sprite(img=grey_img, x=x, y=y, batch=batch, subpixel=True))

    else:
        if blocks:
            blocks.pop(0)

    for block in blocks:
        block.x += dt

    if blocks:
        label.text = f"FPS: {round(fps)}, sprites:{len(blocks)}"


pyglet.clock.schedule_interval(update, 1/120)
pyglet.app.run(1/120)
