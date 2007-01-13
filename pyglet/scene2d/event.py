
from pyglet.scene2d import *

# XXX "evaluated" search knows which properties it is interested in, thus
# when any cell changes we can check the changed property against the
# "listening" "evaluated" searches

class MapFilter:
    def __init__(self, maps, properties):
        self.maps = maps
        self.properties = properties

    def __call__(self, cells):
        ''' Filter by the properties, if any.

        Look in the Cell first, falling back to the Tile if there is one.
        '''
        if not self.properties:
            return cells
        r = []
        for cell in cells:
            for k, v in self.properties.items():
                if k == 'id':
                    if cell.id == v: continue
                    else: break
                if cell.properties[k] == v:
                    continue
                if not hasattr(cell, 'tile') and cell.tile.properties[k] == v:
                    continue
                break
            else:
                r.append(cell)
        return r


class SpriteFilter:
    def __init__(self, sprites, properties):
        self.sprites = sprites
        self.properties = properties

    def __call__(self, sprites):
        ''' Filter by the properties, if any.
        '''
        if not self.properties:
            return sprites
        r = []
        for sprite in sprites:
            for k, v in self.properties.items():
                if k == 'id':
                    if sprite.id == v: continue
                    else: break
                if sprite.properties[k] != v: break
            else:
                r.append(sprite)
        return r


def for_cells(*maps, **criteria):
    def decorate(func):
        if maps: m = maps[0]
        else: m = None
        if m or criteria:
            m = MapFilter(m, criteria)
            if hasattr(func, 'map_filters'):
                if func.map_filters is None:
                    raise ValueError, 'Already seen a @for_sprites()'
                func.map_filters.append(m)
            else:
                func.map_filters = [m]
        else:
            func.map_filters = None

        if not hasattr(func, 'sprite_filters'):
            # search no sprites
            func.sprite_filters = []
        return func
    return decorate

class FitlerPass:
    pass

def for_sprites(*sprites, **criteria):
    def decorate(func):
        if sprites: s = sprites[0]
        else: s = None
        if s or criteria:
            s = SpriteFilter(s, criteria)
            if hasattr(func, 'sprite_filters'):
                if func.sprite_filters is None:
                    raise ValueError, 'Already seen a @for_sprites()'
                func.sprite_filters.append(s)
            else:
                func.sprite_filters = [s]
        else:
            func.sprite_filters = None

        if not hasattr(func, 'map_filters'):
            # search no maps
            func.map_filters = []
        return func
    return decorate

