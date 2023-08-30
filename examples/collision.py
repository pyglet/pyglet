from random import randint

from pyglet import app, clock, window
from pyglet.shapes2d import Rectangle, CollisionRectangle
from pyglet.text import Label

win = window.Window(400, 300, "Collision Detection")
hint = Label(
    "Push the red square,\nso that it touches the blue square!",
    x=200,
    y=150,
    align="center",
    anchor_x="center",
    anchor_y="center",
    multiline=True,
    width=380,
)
rect1 = Rectangle(200, 150, 20, 20, color=(200, 0, 0))
collision1 = CollisionRectangle(200, 150, 20, 20)
rect2 = Rectangle(200, 150, 10, 10, color=(0, 0, 200))
rect2.position = randint(20, 380), randint(20, 280)
collision2 = CollisionRectangle(rect2.x, rect2.y, 10, 10)


@win.event
def on_mouse_motion(x, y, dx, dy):
    global can_drag
    if (x, y) in rect1:
        rect1.color = (255, 0, 0)
    else:
        rect1.color = (200, 0, 0)
    if (x, y) in rect1:
        hint.visible = False
        rect1.x += dx
        rect1.y += dy
        collision1.position = rect1.position


@win.event
def on_draw():
    win.clear()
    rect1.draw()
    rect2.draw()
    hint.draw()


def update(dt):
    if collision1.is_collide(collision2):
        rect2.position = randint(20, 380), randint(20, 280)
        collision2.position = rect2.position


if __name__ == "__main__":
    clock.schedule_interval(win.draw, 1 / 60)
    clock.schedule_interval(update, 1 / 30)
    app.run()
