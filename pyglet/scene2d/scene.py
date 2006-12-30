class Scene:
    def __init__(self, maps=[], sprites=[]):
        self.maps = maps
        self.sprites = sprites
 
    def animate(self, dt):
        ' call .animate on all sprites and tiles '
