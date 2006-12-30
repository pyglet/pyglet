
import pyglet.window
import pyglet.window.event
import pyglet.text
import pyglet.scene2d
import pyglet.clock

w = pyglet.window.Window(width=300, height=300)
f = pyglet.text.Font('Bitstream Vera Sans Mono', 26)
r = f.render
m = pyglet.scene2d.Map(32, 32,
    images=[map(r, 'adg'), map(r, 'beh'), map(r, 'cfi')])
s = pyglet.scene2d.Scene(maps=[m])
r = pyglet.scene2d.FlatRenderer(s, 0, 0, 300, 300)

class running(pyglet.window.event.ExitHandler):
    def __init__(self, fps=60):
        self.clock = pyglet.clock.Clock(fps)
    def __nonzero__(self):
        if self.exit: return False
        self.clock.tick()
        return True
running = running()
w.push_handlers(running)

while running:
    print 'FPS: %s\r'%running.clock.get_fps(),
    w.switch_to()
    w.dispatch_events()
    r.draw((0, 0))
    w.flip()

