class Scene:
    def __init__(self, maps=None, sprites=None):
        if maps is None:
            maps = []
        self.maps = maps
        if sprites is None:
            sprites = []
        self.sprites = sprites
 
    def animate(self, dt):
        ' call .animate on all sprites and tiles '
