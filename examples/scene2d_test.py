'''Usage: %s <arguments>

 -x h           draw a hex grid
 -r w[,h]       draw a rect grid
 -s w,h         map size in cells (default=5,5)
 -l             render with lines (default)
 -c             render with checkers (alternating light/dark grey)
 -f             render flat (default)
 -o             render orthographic projection
 -a sx,sy,sz    render axiometric projection (scaled in x, y, z)
 -p ex,ey,ez    render perspective projection (specify eye offset)
 -h             this help

Samples:
--hex=32
      draw a hex grid, cell height 32
--rect=32
      draw a rect grid, width and height 32
--rect=16,32 --size=10,10
      draw a 10x10 rect grid, width and height 32

Press "s" to save the grid off a file. 
'''

import sys, getopt, os

from pyglet.GL.VERSION_1_1 import *
import pyglet.scene2d
import pyglet.window
import pyglet.window.event
import pyglet.text
import pyglet.clock
import pyglet.image

try:
    optlist, args = getopt.getopt(sys.argv[1:], 'x:r:s:foa:p:hlc')
except getopt.GetoptError, error:
    print error
    print __doc__%sys.argv[0]
    sys.exit()

klass = None
size = (5, 5)
style = 'lines'
renderer = pyglet.scene2d.FlatRenderer
filename = { 's': 'lines', 'r': 'flat' }
for opt, value in optlist:
    if opt == '-x':
        klass = pyglet.scene2d.HexMap
        args = [int(value)]
        filename['x'] = 'hex(%d)'%args[0]
    elif opt == '-r':
        klass = pyglet.scene2d.Map
        args = map(int, value.split(','))
        if len(args) == 1:
            args *= 2
        filename['x'] = 'rect(%dx%d)'%tuple(args)
    elif opt == '-l':
        style = 'lines'
    elif opt == '-c':
        style = 'checkered'
    elif opt == '-s':
        size = map(int, value.split(','))
        filename['e'] = '%dx%d'%tuple(size)
    elif opt == '-f':
        renderer = pyglet.scene2d.FlatRenderer
        filename['r'] = 'flat'
    elif opt == '-o':
        renderer = pyglet.scene2d.AxiometricRenderer
        scale = (1, 1, 1)
        filename['r'] = 'iso'
    elif opt == '-a':
        renderer = pyglet.scene2d.AxiometricRenderer
        scale = map(float, value.split(','))
        filename['r'] = 'axio(%g,%g,%g)'%scale
    elif opt == '-p':
        renderer = pyglet.scene2d.PerspectiveRenderer
        eye = map(int, value.split(','))
        filename['r'] = 'persp(%g,%g,%g)'%eye
    elif opt == '-h':
        print __doc__%sys.argv[0]
        sys.exit()

filename['s'] = style
filename = '%(x)s-%(e)s-%(s)s-%(r)s'%filename

if klass is None:
    print 'ERROR: -x or -r required'
    print __doc__%sys.argv[0]
    sys.exit()

mw, mh = size
kw = dict(images=[[None]*mh]*mw)
m = klass(*args, **kw)

w = pyglet.window.Window(width=m.pxw, height=m.pxh)

f = pyglet.text.Font('Bitstream Vera Sans Mono', 26)
r = f.render

mw, mh = size
kw = dict(images=[
    [r(chr(65 + i + mw * j)) for i in range(mh)]
        for j in range(mw)])
m = klass(*args, **kw)

s = pyglet.scene2d.Scene(maps=[m])
r = pyglet.scene2d.FlatRenderer(s, 0, 0, m.pxw, m.pxh)

class running(pyglet.window.event.ExitHandler):
    def __init__(self, fps=5):
        self.clock = pyglet.clock.Clock(fps)
    def __nonzero__(self):
        if self.exit: return False
        self.clock.tick()
        return True
    def on_text(self, text):
        if text != 's': return pyglet.window.event.EVENT_UNHANDLED
        image = pyglet.image.BufferImage().get_raw_image()
        fn = filename + '.png'
        n = 1
        while os.path.exists(fn):
            fn = filename + str(n) + '.png'
            n += 1
        print 'Saving to %s...'%fn
        image.save(fn)

running = running()
w.push_handlers(running)

while running:
    w.switch_to()
    w.dispatch_events()
    glClear(GL_COLOR_BUFFER_BIT)
    r.debug((0,0), style)
    w.flip()

