'''
Code by Richard Jones, released into the public domain.

Beginnings of something like http://en.wikipedia.org/wiki/Thrust_(video_game)
'''
import sys
import math

import euclid

import primitives

import pyglet
from pyglet.window import key
from pyglet.gl import *

window = pyglet.window.Window(fullscreen='-fs' in sys.argv)

GRAVITY = -200

class Game(object):
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        self.ship = Ship(window.width//2, window.height//2, self.batch)
        self.debug_text = pyglet.text.Label('debug text', x=10, y=window.height-40, batch=self.batch)

    def on_draw(self):
        window.clear()
        self.batch.draw()

    def update(self, dt):
        self.ship.update(dt)


class Ship(object):
    def __init__(self, x, y, batch):
        self.position = euclid.Point2(x, y)
        self.velocity = euclid.Point2(0, 0)
        self.angle = math.pi/2

        self.batch = batch
        self.lines = batch.add(6, GL_LINES, primitives.SmoothLineGroup(),
            ('v2f', (0, 0) * 6),
            ('c4B', (255, 255, 255, 255) * 6))

        self.ball_position = euclid.Point2(window.width/2, window.height/4)
        self.ball_velocity = euclid.Point2(0, 0)
        self.ball_lines = primitives.add_circle(batch, 0, 0, 20, (255, 255, 255, 255), 20)
        self._ball_verts = list(self.ball_lines.vertices)
        self._update_ball_verts()

        self.join_active = False
        self.join_line = None

        self.joined = False

    def update(self, dt):
        self.angle += (keyboard[key.LEFT] - keyboard[key.RIGHT]) * math.pi * dt
        r = euclid.Matrix3.new_rotate(self.angle)
        if keyboard[key.UP]:
            thrust = r * euclid.Vector2(600, 0)
        else:
            thrust = euclid.Vector2(0, 0)

        # attempt join on spacebar press
        s_b = self.position - self.ball_position
        if keyboard[key.SPACE] and abs(s_b) < 100:
            self.join_active = True

        if not self.joined:
            # simulation is just the ship

            # apply thrust to the ship directly
            thrust.y += GRAVITY

            # now figure my new velocity
            self.velocity += thrust * dt

            # calculate new line endpoints
            self.position += self.velocity * dt

        else:
            # simulation is of a rod with ship and one end and ball at other
            n_v = s_b.normalized()
            n_t = thrust.normalized()

            # figure the linear acceleration, velocity & move
            d = abs(n_v.dot(n_t))
            lin = thrust * d
            lin.y += GRAVITY
            self.velocity += lin * dt
            self.cog += self.velocity * dt

            # now the angular acceleration
            r90 = euclid.Matrix3.new_rotate(math.pi/2)
            r_n_t = r90 * n_t
            rd = n_v.dot(r_n_t)
            self.ang_velocity -= abs(abs(thrust)) * rd * 0.0001
            self.join_angle += self.ang_velocity * dt

            # vector from center of gravity our to either end
            ar = euclid.Matrix3.new_rotate(self.join_angle)
            a_r = ar * euclid.Vector2(self.join_length/2, 0)

            # set the ship & ball positions
            self.position = self.cog + a_r
            self.ball_position = self.cog - a_r

            self._update_ball_verts()

        if self.join_active:
            if abs(s_b) >= 100 and not self.joined:
                self.joined = True
                h_s_b = s_b / 2
                self.cog = self.position - h_s_b
                self.join_angle = math.atan2(s_b.y, s_b.x)
                self.join_length = abs(s_b)

                # mass just doubled, so slow linear velocity down
                self.velocity /= 2

                # XXX and generate some initial angular velocity based on
                # XXX ship current velocity
                self.ang_velocity = 0

            # render the join line
            l = [
                self.position.x, self.position.y,
                self.ball_position.x, self.ball_position.y
            ]
            if self.join_line:
                self.join_line.vertices[:] = l
            else:
                self.join_line = self.batch.add(2, GL_LINES, primitives.SmoothLineGroup(),
                    ('v2f', l), ('c4B', (255, 255, 255, 255) * 2))

        # update the ship verts
        bl = r * euclid.Point2(-25, 25)
        t = r * euclid.Point2(25, 0)
        br = r * euclid.Point2(-25, -25)
        x, y = self.position
        self.lines.vertices[:] = [
            x+bl.x, y+bl.y, x+t.x, y+t.y,
            x+t.x, y+t.y, x+br.x, y+br.y,
            x+br.x, y+br.y, x+bl.x, y+bl.y,
        ]

    def _update_ball_verts(self):
        # update the ball for its position
        l = []
        x, y = self.ball_position
        for i, v in enumerate(self._ball_verts):
            if i % 2:
                l.append(int(v + y))
            else:
                l.append(int(v + x))
        self.ball_lines.vertices[:] = l

g = Game()

window.push_handlers(g)
pyglet.clock.schedule(g.update)

keyboard = key.KeyStateHandler()
window.push_handlers(keyboard)

pyglet.app.run()

