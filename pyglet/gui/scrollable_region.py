from pyglet.gui.frame import Frame
from pyglet.gui.layout import LayoutCell
from pyglet.gui.widgets import Slider
from pyglet.gl import *
from pyglet.math import Vec3

class ScrollableRegion(LayoutCell):

    class __WindowDummy:
        def push_handlers(s, v):
            pass

    def __init__(self, x, y, width, height, window,
                 slider_base=(230, 230, 230, 255),
                 slider_knob=(150, 150, 150, 255),
                 vertical=True, horizontal=True,
                 slider_width=20):
        
        self._slider_width = slider_width
        self._rect = (x, y, width, height)

        if horizontal:
            self._horizontal_slider = Slider(
                0,0, width, self._slider_width,
                base=slider_base, knob=slider_knob, orientation='horizontal')
            self._horizontal_slider.set_handler('on_change', self._on_horizontal_change)
        else:
            self._horizontal_slider = None

        if vertical:
            self._vertical_slider = Slider(
                0,0, self._slider_width, height,
                base=slider_base, knob=slider_knob, orientation='vertical')
            self._vertical_slider.value = 1
            self._vertical_slider.set_handler('on_change', self._on_vertical_change)
        else:
            self._vertical_slider = None

        self._hoffset = self._voffset = 0

        super().__init__({
            'content-alignment': ('left', 'top'),
            'padding': (0, slider_width if vertical else 0, slider_width if horizontal else 0, 0)
        })

        self._window = window
        self._window.push_handlers(self)

        self.frame = Frame(ScrollableRegion.__WindowDummy(), order=4)

        self.realign((x, y, width, height))

    @LayoutCell.x.setter
    def x(self, value):
        self.realign((value, self.y, self.width, self.height))

    @LayoutCell.y.setter
    def y(self, value):
        self.realign((self.x, value, self.width, self.height))
    
    @LayoutCell.position.setter
    def position(self, value):
        self.realign((value[0], value[1], self.width, self.height))

    @LayoutCell.width.setter
    def width(self, value):
        self.realign((self.x, self.y, value, self.height))

    @LayoutCell.height.setter
    def height(self, value):
        self.realign((self.x, self.y, self.width, value))
    
    @LayoutCell.size.setter
    def size(self, value):
        self.realign((self.x, self.y, value[0], value[1]))

    @property
    def aabb(self):
        return self.x, self.y, self.x + self.width, self.y + self.height
    
    @property
    def horizontal(self):
        return self._horizontal_slider is not None
    
    @property
    def vertical(self):
        return self._vertical_slider is not None
    
    def realign(self, new_rect=None):
        super().realign(new_rect)
        if self.horizontal:
            vrt_offset = self._slider_width if self.vertical else 0
            self._horizontal_slider.position = (self.x, self.y)
            self._horizontal_slider.size = (self.width - vrt_offset, self._slider_width)
        if self.vertical:
            hor_offset = self._slider_width if self.horizontal else 0
            self._vertical_slider.position = (self.x + self.width - self._slider_width, self.y + hor_offset)
            self._vertical_slider.size = (self._slider_width, self.height - hor_offset)
        self.on_content_bounds_updated()

    def on_content_bounds_updated(self):
        if self.content is None: return

        self.frame.on_widgets_realign()
        if self.horizontal and self.content.width > 0:
            self._horizontal_slider.knob_size = min(
                self._horizontal_slider.width, 
                int(self.width / self.content.width * self._horizontal_slider.width)
            )
        if self.vertical and self.content.height > 0:
            self._vertical_slider.knob_size = min(
                self._vertical_slider.height,
                int(self.height / self.content.height * self._vertical_slider.height)
            )

    def draw(self):
        if self._background is not None:
            self._background.draw()

        if self.content is not None:
            glEnable(GL_SCISSOR_TEST)
            
            glScissor(self.x, 
                      self.y + (self._slider_width if self.horizontal else 0), 
                      self.width - (self._slider_width if self.vertical else 0), 
                      self.height - (self._slider_width if self.horizontal else 0)
            )

            origin_matrix = self._window.view
            self._window.view = self._window.view.translate(Vec3(self._hoffset, self._voffset, 0))
            self.content.draw()
            self._window.view = origin_matrix

            glDisable(GL_SCISSOR_TEST)

        if self.horizontal:
            self._horizontal_slider.draw()
        
        if self.vertical:
            self._vertical_slider.draw()

    def _on_vertical_change(self, val):
        if self.content is None: return
        if self.content.height > self.height - self._style["padding-bottom"]:
            self._voffset = int((self._content.height - self.height + self._style["padding-bottom"]) * (1 - val))
        else:
            self._voffset = 0

    def _on_horizontal_change(self, val):
        if self.content is None: return
        if self.content.width > self.width - self._style["padding-right"]:
            self._hoffset = -int((self._content.width - self.width + self._style["padding-right"]) * val)
        else:
            self._hoffset = 0
        
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if not self._check_hit(x, y): return
        if self.horizontal and self._horizontal_slider._check_hit(x, y):
            self._vertical_slider.value += 50.0 / self.content.height
        elif self.vertical and self._vertical_slider._check_hit(x, y):
            self._horizontal_slider.value += 50.0 / self.content.width
        else:
            self.frame.on_mouse_scroll(x - self._hoffset, y - self._voffset, scroll_x, scroll_y)

    def on_mouse_press(self, x, y, buttons, modifiers):
        if not self._check_hit(x, y): return
        if self.horizontal and self._horizontal_slider._check_hit(x, y):
            self._horizontal_slider.on_mouse_press(x, y, buttons, modifiers)
        elif self.vertical and self._vertical_slider._check_hit(x, y):
            self._vertical_slider.on_mouse_press(x, y, buttons, modifiers)
        else:
            self.frame.on_mouse_press(x - self._hoffset, y - self._voffset, buttons, modifiers)

    def on_mouse_release(self, x, y, buttons, modifiers):
        if not self._check_hit(x, y): return
        if self.horizontal:
            self._horizontal_slider.on_mouse_release(x, y, buttons, modifiers)
        if self.vertical:
            self._vertical_slider.on_mouse_release(x, y, buttons, modifiers)
        self.frame.on_mouse_release(x - self._hoffset, y - self._voffset, buttons, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not self._check_hit(x, y): return
        if self.horizontal:
            self._horizontal_slider.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
        if self.vertical:
            self._vertical_slider.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
        self.frame.on_mouse_drag(x - self._hoffset, y - self._voffset, dx, dy, buttons, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        if not self._check_hit(x, y): return
        if self.horizontal:
            self._horizontal_slider.on_mouse_motion(x, y, dx, dy)
        if self.vertical:
            self._vertical_slider.on_mouse_motion(x, y, dx, dy)
        self.frame.on_mouse_motion(x - self._hoffset, y - self._voffset, dx, dy)

    def on_text(self, text):
        self.frame.on_text(text)

    def on_text_motion(self, motion):
        self.frame.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        self.frame.on_text_motion_select(motion)

    def on_key_press(self, symbol, modifiers):
        self.frame.on_key_press(symbol, modifiers)
    
    def on_key_release(self, symbol, modifiers):
        self.frame.on_key_release(symbol, modifiers)

    def _check_hit(self, x, y):
        return self.x < x < self.x + self.width and self.y < y < self.y + self.height
