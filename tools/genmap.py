'''Usage: %s <arguments>

 -h h           draw hexes with given height in a rectangular grid
 -x h           draw hexes with given height in a hex grid
 -r w[,h]       draw a rect grid
 -s w,h         map size in cells (default=5,5)
 -f             render flat (default)
 -o             render orthographic projection
 -a sx,sy,sz    render axiometric projection (scaled in x, y, z)
 -h             this help

Samples:
-h32 -p2
      draw hexes in a rect grid, cell height 32
-x32 -s5,15
      draw a hex grid, cell height 32
-x32
      draw a rect grid, width and height 32
-r16,32 -s10,10
      draw a 10x10 rect grid, width and height 32

Press "s" to save the grid off a file. 
'''

import sys, getopt, os

import pyglet.ext.scene2d
import pyglet.window
import pyglet.window.event
from pyglet import clock
import pyglet.image

from pyglet.ext.scene2d.debug import gen_hex_map, gen_rect_map, gen_recthex_map

try:
    optlist, args = getopt.getopt(sys.argv[1:], 'x:r:s:foa:p:h:')
except getopt.GetoptError, error:
    print error
    print __doc__%sys.argv[0]
    sys.exit()

size = (5, 5)
renderer = pyglet.ext.scene2d.FlatView
maptype = None
filename = { 'r': 'flat', 'e': '5x5' }
for opt, value in optlist:
    if opt == '-h':
        maptype = 'recthex'
        ch = int(value)
        filename['x'] = 'recthex(%d)'%ch
    elif opt == '-x':
        maptype = 'hex'
        ch = int(value)
        filename['x'] = 'hex(%d)'%ch
    elif opt == '-r':
        maptype = 'rect'
        args = map(int, value.split(','))
        if len(args) == 1:
            args *= 2
        cw, ch = args
        filename['x'] = 'rect(%dx%d)'%tuple(args)
    elif opt == '-s':
        size = map(int, value.split(','))
        filename['e'] = '%dx%d'%tuple(size)
    elif opt == '-f':
        renderer = pyglet.ext.scene2d.FlatView
        filename['r'] = 'flat'
    elif opt == '-o':
        renderer = pyglet.ext.scene2d.AxiometricView
        scale = (1, 1, 1)
        filename['r'] = 'iso'
    elif opt == '-a':
        renderer = pyglet.ext.scene2d.AxiometricView
        scale = map(float, value.split(','))
        filename['r'] = 'axio(%g,%g,%g)'%scale

if maptype is None:
    print 'ERROR: -x or -r required'
    print __doc__%sys.argv[0]
    sys.exit()

filename = '%(x)s-%(e)s-%(r)s'%filename

w = pyglet.window.Window(width=1, height=1, visible=False, alpha_size=8)

mw, mh = size
if maptype == 'recthex':
    m = gen_recthex_map([[{}]*mh]*mw, ch)
elif maptype == 'hex':
    m = gen_hex_map([[{}]*mh]*mw, ch)
else:
    m = gen_rect_map([[{}]*mh]*mw, cw, ch)
pxw = m.pxw
pxh = m.pxh
w.set_size(width=pxw, height=pxh)
w.set_visible()
r = pyglet.ext.scene2d.FlatView(0, 0, pxw, pxh, layers=[m])

class SaveHandler:
    def on_text(self, text):
        if text != 's': return pyglet.window.event.EVENT_UNHANDLED
        image = pyglet.image.BufferImage().get_raw_image()
        fn = filename + '.png'
        n = 1
        while os.path.exists(fn):
            fn = filename + str(n) + '.png'
            n += 1
        print "Saving to '%s'"%fn
        image.save(fn)
w.push_handlers(SaveHandler())

clock.set_fps_limit(10)
while not w.has_exit:
    clock.tick()
    w.dispatch_events()
    r.clear((0,0,0,0))
    r.draw()
    w.flip()

