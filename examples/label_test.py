from pyglet import window
from pyglet import font
from pyglet import text

w = window.Window()

t = text.Label('this is a test', x=100, y=100)

# the following is needed for it to display
#t.x, t.y = 100, 100
#t.width = w.width
#t.height = w.height

while not w.has_exit:
    w.dispatch_events()
    w.clear()
    t.draw()
    w.flip()

