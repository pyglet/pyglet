#!/usr/bin/python
# $Id:$

import random
import sys

from pyglet.gl import *
from pyglet import clock
from pyglet import font
from pyglet import graphics
from pyglet import window


MAX_PARTICLES = 1000
if len(sys.argv) > 1:
    MAX_PARTICLES = int(sys.argv[1])
MAX_ADD_PARTICLES = 100
GRAVITY = -100

win = window.Window(vsync=False)
batch = graphics.Batch()
particles = []

def add_particles():
    particle = batch.add(1, GL_POINTS, None, 
        ('v2f/stream', [win.width/2, 0]))
    particle.dx = (random.random() - .5) * win.width/4
    particle.dy = win.height * (.5 + random.random() * .2)
    particle.dead = False
    particles.append(particle)

def update_particles():
    global particles
    for particle in particles:
        particle.dy += GRAVITY * dt
        vertices = particle.vertices
        vertices[0] += particle.dx * dt
        vertices[1] += particle.dy * dt
        if vertices[1] <= 0:
            particle.delete()
            particle.dead = True
    particles = [p for p in particles if not p.dead]

stats_text = font.Text(font.load('', 12), '', 
                       x=win.width, y=0,
                       halign='right')

def update_stats(dt):
    np = len(particles)
    usage = particles[0].domain.allocator.get_usage()
    fragmentation = particles[0].domain.allocator.get_fragmentation()
    blocks = len(particles[0].domain.allocator.starts)
    stats_text.text = \
        'Particles: %d  Blocks: %d  Usage: %d%%  Fragmentation: %d%%' % \
        (np, blocks, usage * 100, fragmentation * 100)
clock.schedule_interval(update_stats, 1)

fps_text = clock.ClockDisplay()

while not win.has_exit:
    win.dispatch_events()
    dt = clock.tick()

    update_particles()
    for i in range(min(MAX_ADD_PARTICLES, MAX_PARTICLES - len(particles))):
        add_particles()
    
    win.clear()
    batch.draw()

    stats_text.draw()
    fps_text.draw()

    win.flip()
