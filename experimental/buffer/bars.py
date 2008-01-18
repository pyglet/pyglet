#!/usr/bin/python
# $Id:$

import random
import sys

from pyglet.gl import *
from pyglet import clock
from pyglet import font
from pyglet import graphics
from pyglet import window

BARS = 100
if len(sys.argv) > 1:
    BARS = int(sys.argv[1])
MIN_BAR_LENGTH = 4
MAX_BAR_LENGTH = 100
BAR_SEGMENT_HEIGHT = 10

UPDATE_PERIOD = 0.01

win = window.Window(vsync=False)
batch = graphics.Batch()
bars = []

colors = [
    [170, 0, 0],
    [0, 255, 100],
    [80, 100, 255],
    [40, 180, 180],
    [200, 255, 100],
    [255, 70, 200],
    ]

def create_bars():
    width = win.width / float(BARS)
    for i in range(BARS):
        position = [i * width, 0, # degenerate
                    i * width, 0,
                    (i + 1) * width, 0,
                    (i + 1) * width, 0 # degenerate
                   ]
        color = colors[i % len(colors)] * 4

        bar = batch.add(4, GL_TRIANGLE_STRIP, None, 
            ('v2f/dynamic', position),
            ('c3B/dynamic', color))
        bars.append(bar)


def update_bars():
    for bar in bars:
        old_length = bar.count
        length = random.randint(MIN_BAR_LENGTH, MAX_BAR_LENGTH)
        bar.resize(length)
        vertices = bar.vertices

        # Update new vertices (overwrite old degenerate)
        for i in range((old_length - 1) * 2, length * 2):
            if i & 1: # y
                vertices[i] = BAR_SEGMENT_HEIGHT * (i // 4)
            else: # x
                vertices[i] = vertices[i - 4]

        # Update top degenerate (first degenerate is never modified)
        vertices[-2:] = vertices[-4:-2]

        # Update colors
        if length > old_length:
            bar.colors[old_length*3:length*3] = \
                bar.colors[:3] * (length - old_length)

stats_text = font.Text(font.load('', 12, bold=True), '', 
                       x=win.width, y=0,
                       halign='right')

def update_stats(dt):
    np = len(bars)
    usage = bars[0].domain.allocator.get_usage()
    fragmentation = bars[0].domain.allocator.get_fragmentation()
    blocks = len(bars[0].domain.allocator.starts)
    stats_text.text = \
        'Bars: %d  Blocks: %d  Usage: %d%%  Fragmentation: %d%%' % \
        (np, blocks, usage * 100, fragmentation * 100)
clock.schedule_interval(update_stats, 1)

fps_text = clock.ClockDisplay(color=(1, 1, 1, 1))

create_bars()

update_time = 0.

while not win.has_exit:
    win.dispatch_events()
    dt = clock.tick()
    dt = min(dt, 0.05)

    update_time += dt
    if update_time > UPDATE_PERIOD:
        update_bars()
        update_time -= UPDATE_PERIOD
    
    win.clear()
    batch.draw()

    stats_text.draw()
    fps_text.draw()

    win.flip()
