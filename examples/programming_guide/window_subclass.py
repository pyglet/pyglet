#!/usr/bin/env python

'''Demonstrates a useful pattern for pyglet applications: subclassing Window.
'''

from pyglet import font
from pyglet import window

class HelloWorldWindow(window.Window):
    def __init__(self):
        super(HelloWorldWindow, self).__init__()

        ft = font.load('Arial', 36)
        self.text = font.Text(ft, 'Hello, World!')

    def draw(self):
        self.text.draw()

    def run(self):
        while not self.has_exit:
            self.dispatch_events()

            self.clear()
            self.draw()
            self.flip()

if __name__ == '__main__':
    HelloWorldWindow().run()
