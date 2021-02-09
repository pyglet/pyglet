"""
Simple example showing some animated shapes
"""
import math
import pyglet
from pyglet import shapes


class ShapesDemo(pyglet.window.Window):

    def __init__(self, width, height):
        super().__init__(width, height, "Shapes")
        self.time = 0
        self.batch = pyglet.graphics.Batch()

        self.circle = shapes.Circle(360, 240, 100, color=(255, 225, 255), batch=self.batch)
        self.circle.opacity = 127

        # Rectangle with center as anchor
        self.square = shapes.Rectangle(360, 240, 200, 200, color=(55, 55, 255), batch=self.batch)
        self.square.anchor_x = 100
        self.square.anchor_y = 100

        # Large transparent rectangle
        self.rectangle = shapes.Rectangle(0, 190, 720, 100, color=(255, 22, 20), batch=self.batch)
        self.rectangle.opacity = 64

        self.line = shapes.Line(0, 0, 0, 480, width=4, color=(200, 20, 20), batch=self.batch)

        self.triangle = shapes.Triangle(10, 10, 190, 10, 100, 150, color=(10, 255, 10), batch=self.batch)
        self.triangle.opacity = 175

        self.arc = shapes.Arc(50, 300, radius=40, segments=25, angle=4, color=(255, 255, 255), batch=self.batch)

    def on_draw(self):
        """Clear the screen and draw shapes"""
        self.clear()
        self.batch.draw()

    def update(self, delta_time):
        """Animate the shapes"""
        self.time += delta_time
        self.square.rotation = self.time * 15
        self.rectangle.y = 200 + math.sin(self.time) * 190
        self.circle.radius = 175 + math.sin(self.time * 1.17) * 30
        self.line.position = (
            360 + math.sin(self.time * 0.81) * 360,
            0,
            360 + math.sin(self.time * 1.34) * 360,
            480,
        )
        self.arc.rotation = self.time * 30


if __name__ == "__main__":
    demo = ShapesDemo(720, 480)
    pyglet.clock.schedule_interval(demo.update, 1/30)
    pyglet.app.run()
