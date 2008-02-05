#!/usr/bin/python
# $Id:$

import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from pyglet.gl import *
from pyglet import clock
from pyglet import font
from pyglet import resource
from pyglet import window
from pyglet.window import key, mouse

from pyglet import graphics
from pyglet.text import attributed
from pyglet.text import caret as caret_module
from pyglet.text import style
from pyglet.text import document
from pyglet.text import layout

click_time = 0
click_count = 0

def main():
    w = window.Window(vsync=False, resizable=True)
    w.set_mouse_cursor(w.get_system_mouse_cursor('text'))

    @w.event
    def on_key_press(symbol, modifiers):
        if sys.platform == 'darwin':
            accel = key.MOD_COMMAND
        else:
            accel = key.MOD_CTRL

        if modifiers & accel:
            if symbol == key.B:
                toggle_style('bold')
            elif symbol == key.I:
                toggle_style('italic')
            elif symbol in (key.EQUAL, key.NUM_ADD):
                add_font_size(2)
            elif symbol in (key.MINUS, key.NUM_SUBTRACT):
                add_font_size(-2)

        if symbol == key.ESCAPE:
            w.has_exit = True

    def toggle_style(attribute):
        old = caret.get_style(attribute)
        if old == style.INDETERMINATE:
            value = True
        else:
            value = not old
        caret.set_style({attribute: value})

    def add_font_size(size):
        old_size = caret.get_style('font_size')
        if old_size in (style.INDETERMINATE, None):
            old_size = 12
        caret.set_style({'font_size': old_size + size})

    def on_resize(width, height):
        text.x = border
        text.y = height - border
        text.width = width - border * 2
        text.height = height - border * 2
        caret._update()
    w.push_handlers(on_resize)

    if len(sys.argv) > 1:
        content = open(sys.argv[1]).read()
    else:
        content = resource.file('info.att').read()

    # Draw to this border so we can test clipping.
    border = 50

    batch = graphics.Batch()
    doc = attributed(content)
    text = layout.IncrementalTextLayout(doc,  
                    w.width-border*2, w.height-border*2, multiline=True,
                    batch=batch) 
    caret = caret_module.Caret(text)
    caret.color = (0, 0, 0)
    caret.visible = True
    caret.position = 0
    w.push_handlers(caret)

    fps = clock.ClockDisplay(font=font.load('', 10, dpi=96), 
        color=(0, 0, 0, 1), interval=1., format='FPS: %(fps)d')
    fps.label.x = 2
    fps.label.y = 15
    stats_text = font.Text(font.load('', 10, dpi=96), '', 
        x=2, y=2, color=(0, 0, 0, 1))
   
    def update_stats(dt):
        states = batch.state_map.values()
        usage = 0.
        blocks = 0
        domains = 0

        fragmentation = 0.
        free_space = 0.
        capacity = 0.

        for state in states:
            for domain in state.values():
                domains += 1
                free_space += domain.allocator.get_free_size()
                fragmentation += domain.allocator.get_fragmented_free_size()
                capacity += domain.allocator.capacity
                blocks += len(domain.allocator.starts)
        if free_space:
            fragmentation /= free_space
        else:
            fragmentation = 0.
        free_space /= capacity
        usage = 1. - free_space
        stats_text.text = \
            'States: %d  Domains: %d  Blocks: %d  Usage: %d%%  Fragmentation: %d%%' % \
            (len(states), domains, blocks, usage * 100, fragmentation * 100)
    clock.schedule_interval(update_stats, 1) 

    glClearColor(1, 1, 1, 1)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
    while not w.has_exit:
        clock.tick()
        w.dispatch_events()
        w.clear()
        batch.draw()
        fps.draw()
        stats_text.draw()

        glPushAttrib(GL_CURRENT_BIT)
        glColor3f(0, 0, 0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glRectf(border - 2, border - 2, 
                w.width - border + 4, w.height - border + 4)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glPopAttrib()

        w.flip()

if __name__ == '__main__':
    main()
