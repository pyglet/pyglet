
from pyglet.scene2d import *

# XXX "evaluated" search knows which properties it is interested in, thus
# when any cell changes we can check the changed property against the
# "listening" "evaluated" searches

class MapSearch:
    def __init__(self, map, properties):
        self.map = map      # XXX this has to be filtered during cell
                            # collection, not after
        self.properties = properties
        self.result = [] # XXX ...

    def __call__(self, objs):
        if not self.properties: return objs
        r = []
        for obj in objs:
            for k, v in self.properties.items():
                if obj.properties[k] != v:
                    break
            else:
                r.append(obj)
        return r

    def update(self, cell):
        # add to / remove from / don't touch self.result
        raise NotImplemented()

def event(dispatcher):
    def decorate(func):
        if not hasattr(func, 'limit'):
            func.limit = None
        dispatcher.push_handlers(func)
    return decorate

def for_cells(obj, **properties):
    def decorate(func):
        func.limit = MapSearch(obj, properties)
        # XXX "compile" limit
        return func
    return decorate

def for_sprites(obj, **properties):
    def decorate(func):
        # XXX "compile" limit
        func.limit = (obj, properties)
        return func
    return decorate

"""
@event(view)
@for_cells(map, type='grass')
@for_cells(map, is_base=True)
def on_mouse_enter(cells, x, y):

def on_mouse_leave(cells):

@event(view)
@for_sprites([list of sprites])
def on_mouse_enter(sprites, x, y, button, modifier):

def on_mouse_release(sprites, x, y, button, modifier):

def on_mouse_drag(sprites, x, y, dx, dy, button, modifier):

def on_view_enter(cells):
    ''' sprite or cell has entered the View (even if potentially obscured by
    another cell / sprite '''

def on_view_leave(cells):
    ' sprite or cell has left the View '

"""
