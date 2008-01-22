from pyglet import window
from pyglet import text
from pyglet import clock
from pyglet import font

w = window.Window(fullscreen=True)

class Timer(text.Label):
    def stop(self):
        self.__time = 0
    def reset(self):
        self.__time = 0
        self.__running = False
        self.text = '00:00'
    def animate(self, dt):
        if self.__running:
            self.__time += dt
            m, s = divmod(self.__time, 60)
            self.text = '%02d:%02d'%(m, s)

    def on_text(self, text):
        if text == ' ':
            self.__running = not self.__running
            return True
        return False

ft = font.load('', 360)
timer = Timer('00:00', ft, x=w.width//2, y=w.height//2,
    valign='center', halign='center')
timer.reset()
clock.schedule(timer.animate)
w.push_handlers(timer)

while not w.has_exit:
    w.dispatch_events()
    clock.tick()
    w.clear()
    timer.draw()
    w.flip()

