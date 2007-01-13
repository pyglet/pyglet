
from pyglet.scene2d import *

# XXX "evaluated" search knows which properties it is interested in, thus
# when any cell changes we can check the changed property against the
# "listening" "evaluated" searches

class MapSearch:
    def __init__(self, properties):
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
        if not hasattr(func, 'maps'):
            func.maps = None
        if not hasattr(func, 'sprites'):
            func.sprites = None
        dispatcher.push_handlers(func)
    return decorate

def for_cells(*maps, **limit):
    def decorate(func):
        # XXX limits need to stack with the props, maps and sprites args
        func.limit = MapSearch(limit)
        if maps:
            func.maps = maps[0]
        else:
            func.maps = None
        if not hasattr(func, 'sprites'):
            func.sprites = []
        return func
    return decorate

def for_sprites(sprites, **limit):
    def decorate(func):
        # XXX "compile" limit
        func.limit = limit
        func.sprites = sprites
        if not hasattr(func, 'maps'):
            func.maps = []
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
