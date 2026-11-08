import pyglet

class TouchExample:
    COLORS = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (0, 255, 255),
        (255, 255, 0),
        (255, 0, 255),
        (255, 255, 255),
        (128, 128, 128)
    ]
    def __init__(self):
        self.window = pyglet.window.Window(500, 500, caption="Touch Example")
        self.batch = pyglet.graphics.Batch()
        self._counter = 0

        self.touch_circles = {}

        self.window.push_handlers(self)

    def on_draw(self):
        self.window.clear()
        self.batch.draw()

    def on_touch_start(self, pointer_id, x, y, dx, dy, width, height, pressure, scale):
        if pointer_id not in self.touch_circles:
            color = self.COLORS[self._counter]
            self.touch_circles[pointer_id] = pyglet.shapes.Circle(x, y, width, color=color, batch=self.batch)
            self._counter += 1
        else:
            self.touch_circles[pointer_id].position = x, y

    def on_touch_move(self, pointer_id, x, y, dx, dy, width, height, pressure, scale):
        if pointer_id in self.touch_circles:
            circle = self.touch_circles[pointer_id]
            circle.position = x, y
            circle.radius = width

    def on_touch_end(self, pointer_id, x, y, dx, dy, width, height, pressure, scale):
        if pointer_id in self.touch_circles:
            circle = self.touch_circles[pointer_id]
            circle.delete()
            del self.touch_circles[pointer_id]
            self._counter -= 1


touch_example = TouchExample()

pyglet.app.run()
