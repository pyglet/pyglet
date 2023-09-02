from random import randint

from pyglet import app, clock, window
from pyglet.shapes2d import Rectangle, CollisionRectangle
from pyglet.text import Label

win = window.Window(400, 300, "Collision Detection")
hint = Label(
    "Push the red square\nand let it touches the blue square!",
    x=200,
    y=90,
    align="center",
    anchor_x="center",
    anchor_y="center",
    multiline=True,
    width=380,
)
rect1 = Rectangle(200, 150, 20, 20, color=(255, 0, 0))
collision1 = CollisionRectangle(200, 150, 20, 20)
rect2 = Rectangle(200, 150, 20, 20, color=(0, 0, 255))
rect2.position = randint(0, 380), randint(120, 280)
collision2 = CollisionRectangle(rect2.x, rect2.y, 20, 20)

@win.event
def on_mouse_motion(x, y, dx, dy):
    if (x, y) in collision1:
        if hint.visible:
            hint.visible = False
        rect1.x = max(0, min(rect1.x + 1.2 * dx, 380))
        rect1.y = max(0, min(rect1.y + 1.2 * dy, 280))
        collision1.position = rect1.position

@win.event
def on_draw():
    win.clear()
    rect1.draw()
    rect2.draw()
    hint.draw()

def update(dt):
    if collision1.collide(collision2):
        rect2.position = randint(20, 380), randint(20, 280)
        collision2.position = rect2.position

if __name__ == "__main__":
    clock.schedule_interval(win.draw, 1 / 60)
    clock.schedule_interval(update, 1 / 60)
    app.run()
