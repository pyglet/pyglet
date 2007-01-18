
class Layer(object):

    def get(self, px):
        ''' Return object at position px=(x,y).
        Return None if out of bounds.'''
        raise NotImplemented()

    def get_in_region(self, x1, y1, x2, y2):
        '''Return Drawables that are within the pixel bounds specified by
        the bottom-left (x1, y1) and top-right (x2, y2) corners.
        '''
        raise NotImplemented()


class Scene(object):
    __slots__ = 'layers sprites'.split()
    def __init__(self, layers=None, sprites=None):
        if layers is None:
            layers = []
        self.layers = layers

        if sprites is None:
            sprites = []
        self.sprites = sprites
 
