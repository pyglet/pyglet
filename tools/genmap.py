'''Usage: %s <arguments>

 -h h           draw hexes with given height in a rectangular grid
 -x h           draw hexes with given height in a hex grid
 -r w[,h]       draw a rect grid
 -p n           put n pixels padding around each drawn cell
 -s w,h         map size in cells (default=5,5)
 -f             render flat (default)
 -o             render orthographic projection
 -a sx,sy,sz    render axiometric projection (scaled in x, y, z)
 -h             this help

Samples:
-h32 -p2
      draw hexes in a rect grid, cell height 32, padding 2
-x32 -s5,15
      draw a hex grid, cell height 32
-x32
      draw a rect grid, width and height 32
-r16,32 -s10,10
      draw a 10x10 rect grid, width and height 32

Press "s" to save the grid off a file. 
'''

import sys, getopt, os

import pyglet.scene2d
import pyglet.window
import pyglet.window.event
import pyglet.clock
import pyglet.image

from pyglet.scene2d.debug import gen_hex_map, gen_rect_map, gen_recthex_map

try:
    optlist, args = getopt.getopt(sys.argv[1:], 'x:r:s:foa:p:h:p:')
except getopt.GetoptError, error:
    print error
    print __doc__%sys.argv[0]
    sys.exit()

size = (5, 5)
renderer = pyglet.scene2d.FlatView
maptype = None
padding = 0
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
    elif opt == '-p':
        padding = int(value)
    elif opt == '-s':
        size = map(int, value.split(','))
        filename['e'] = '%dx%d'%tuple(size)
    elif opt == '-f':
        renderer = pyglet.scene2d.FlatView
        filename['r'] = 'flat'
    elif opt == '-o':
        renderer = pyglet.scene2d.AxiometricView
        scale = (1, 1, 1)
        filename['r'] = 'iso'
    elif opt == '-a':
        renderer = pyglet.scene2d.AxiometricView
        scale = map(float, value.split(','))
        filename['r'] = 'axio(%g,%g,%g)'%scale

if maptype is None:
    print 'ERROR: -x or -r required'
    print __doc__%sys.argv[0]
    sys.exit()

filename = '%(x)s-%(e)s-%(r)s'%filename

w = pyglet.window.Window(width=1, height=1, visible=False)

mw, mh = size
if maptype == 'recthex':
    m = gen_recthex_map([[{}]*mh]*mw, ch, padding)
elif maptype == 'hex':
    m = gen_hex_map([[{}]*mh]*mw, ch)
else:
    m = gen_rect_map([[{}]*mh]*mw, cw, ch)
w.set_size(width=m.pxw, height=m.pxh)
w.set_visible()
s = pyglet.scene2d.Scene(layers=[m])
r = pyglet.scene2d.FlatView(s, 0, 0, m.pxw, m.pxh, allow_oob=False)

class SaveHandler:
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
w.push_handlers(SaveHandler())

clock = pyglet.clock.Clock(fps_limit=10)
while not w.has_exit:
    clock.tick()
    w.switch_to()
    w.dispatch_events()
    r.clear()
    r.draw()
    w.flip()

