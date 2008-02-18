# desktop tower defense clone
import math
import random

from pyglet import window
from pyglet import image
from pyglet import resource
from pyglet import clock
from pyglet.window import mouse

import view
import tilemap
import spryte

import path

field_cells = '''
+++++++++++EEEEE++++++++++++
+##########.....###########+
+#........................#+
+#........................#+
+#........................#+
+#........................#+
+#........................#+
+#........................#+
+#........................#+
+#........................#+
+#........................#+
S..........................E
S..........................E
S..........................E
S..........................E
S..........................E
+#........................#+
+#........................#+
+#........................#+
+#........................#+
+#........................#+
+#........................#+
+#........................#+
+#........................#+
+#........................#+
+#........................#+
+##########.....###########+
+++++++++++SSSSS++++++++++++
'''.strip()
field_rows = [line.strip() for line in field_cells.splitlines()]

cw = ch = 16
hw = hh = 8
map_height = len(field_rows)
map_width = len(field_rows[0])

win = window.Window(map_width*cw, map_height*ch)

# load / create image resources
blank_image = image.create(cw, ch, image.SolidColorImagePattern((200,)*4))
wall_image = image.create(cw, ch, image.SolidColorImagePattern((100,)*4))
highlight_image = image.create(cw, ch,
    image.SolidColorImagePattern((255, 255, 255, 100)))
enemy_image = image.create(hw, hh,
    image.SolidColorImagePattern((255, 50, 50, 255)))
enemy_image.anchor_x = hw//2
enemy_image.anchor_y = hh//2
turret_image = resource.image('basic-gun.png')
turret_image.anchor_x = 8
turret_image.anchor_y = 8
bullet_image = image.create(3, 3, image.SolidColorImagePattern((0,0,0,255)))
bullet_image.anchor_x = 1
bullet_image.anchor_y = 1

def distance(x1, y1, x2, y2):
    return math.sqrt((x2-x1)**2 + (y2-y1)**2)

class Game(object):
    def __init__(self):
        self.highlight = spryte.Sprite(highlight_image, 0, 0)
        self.show_highlight = False

        # CREATE THE MAP
        self.field = tilemap.Map()
        self.play_field = {}
        l = []
        for y, line in enumerate(field_rows):
            m = []
            l.append(m)
            for x, cell in enumerate(line):
                if cell == '#':
                    m.append(spryte.Sprite(wall_image, x*cw, y*ch,
                        batch=self.field))
                    content = path.Blocker
                else:
                    m.append(spryte.Sprite(blank_image, x*cw, y*ch,
                        batch=self.field))
                    if cell == 'E':
                        content = path.End
                    elif cell == 'S':
                        content = path.Start
                    elif cell == '+':
                        content = path.Blocker
                    else:
                        content = None
                self.play_field[x*2, y*2] = content
                self.play_field[x*2+1, y*2] = content
                self.play_field[x*2, y*2+1] = content
                self.play_field[x*2+1, y*2+1] = content
        self.field.set_cells(cw, ch, l)

        # PATH FOR ENEMIES
        self.path = path.Path.determine_path(self.play_field, map_width*2,
            map_height*2)
        #self.path.dump()

        self.constructions = spryte.SpriteBatch()

        self.enemies = spryte.SpriteBatch()
        self.bullets = spryte.SpriteBatch()

    def spawn_enemies(self):
        # SOME ENEMIES
        starts = []
        ends = set()
        for y, row in enumerate(field_rows):
            for x, cell in enumerate(row):
                if cell == 'S':
                    starts.append((x*2, y*2))
                elif cell == 'E':
                    ends.add((x*2, y*2))

        def create_enemy(dt):
            x, y = random.choice(starts)
            Enemy(x, y, self, ends)
            
        for i in range(10):
            clock.schedule_once(create_enemy, i+1) # +10

    def create_construction(self, x, y):
        x, y = (x // hw)*hw, (y // hh)*hh
        cx, cy = x//hw, y//hh

        cells = (cx, cy), (cx+1, cy), (cx, cy+1), (cx+1, cy+1)

        for cell in cells:
            if self.play_field[cell]:
                return

        # check we're not going to block the only path for any enemy
        if not self.path.test_mod(cells):
            return

        # all ok
        Turret(x, y, self)
        for cell in cells:
            self.play_field[cell] = path.Blocker
        self.path = path.Path.determine_path(self.play_field, map_width*2,
            map_height*2)
        #self.path.dump()
        self.show_highlight = False

    def update(self, dt):
        for shooter in self.constructions:
            shooter.update(dt)

        # build a hash table of enemy positions in the grid
        hit_hash = {}
        for enemy in self.enemies:
            enemy.update(dt)
            x, y = enemy.center
            hpos = ((x // hw)*hw, (y // hh)*hh)
            hit_hash[hpos] = enemy

        # hit the enemies with the bullets
        for bullet in self.bullets:
            bullet.update(dt)
            # bullet position is its center
            x, y = bullet.position
            hpos = ((x // hw)*hw, (y // hh)*hh)
            if hpos in hit_hash:
                enemy = hit_hash[hpos]
                bullet.hit(enemy)
                bullet.delete()

    def draw(self):
        self.field.draw()
        self.constructions.draw()
        self.enemies.draw()
        self.bullets.draw()
        if self.show_highlight:
            self.highlight.draw()

    # CONSTRUCTIONS
    def on_mouse_motion(self, x, y, dx, dy):
        cx, cy = x//hw, y//hh
        try:
            if (self.play_field[cx, cy] or self.play_field[cx+1, cy] or
                    self.play_field[cx, cy+1] or self.play_field[cx+1, cy+1]):
                self.show_highlight = False
                return True
        except KeyError:
            self.show_highlight = False
            return True
        self.show_highlight = True
        self.highlight.position = cx*hw, cy*hh
        return True

    def on_key_press(self, symbol, modifiers):
        if symbol == window.key._1:
            x, y = win._mouse_x, win._mouse_y
            if self.constructions.hit(x, y):
                return False
            self.create_construction(x, y)
            return True
        return False

class Turret(spryte.Sprite):

    range = 75
    reload = 0
    target = None
    rotation_speed = 5

    def __init__(self, x, y, game):
        super(Turret, self).__init__(turret_image, x+8, y+8,
            game=game, batch=game.constructions)

    def update(self, dt):
        sx, sy = self.center
        self.reload = max(0, self.reload - dt)

        if self.target is not None and self.target.health > 0:
            # aim again
            ex, ey = self.target.center
            d = distance(sx, sy, ex, ey)
            if d < self.range:
                shoot = not self.reload
                self.shoot_at(d, self.target, dt, shoot)
                return

        if self.reload:
            return

        self.target = None

        # find a new target
        l = []
        for enemy in self.game.enemies:
            ex, ey = enemy.center
            d = distance(sx, sy, ex, ey)
            if d > self.range:
                continue
            l.append((d, enemy))
        if not l:
            # nothing to shoot at
            return
        l.sort()
        self.shoot_at(l[0][0], l[0][1], dt)

    def shoot_at(self, d, enemy, dt, shoot=True):
        self.target = enemy
        sx, sy = self.center
        ex, ey = enemy.position
        edx, edy = enemy.dx, enemy.dy

        # figure time to hit target
        projectile_speed = 70.
        dt = d / projectile_speed

        # adjust target spot for target's movement
        ex += edx * dt
        ey += edy * dt

        # ok, now figure the vector to hit that spot
        dx = ex - sx
        dy = ey - sy
        magnitude = math.sqrt(dx**2 + dy**2)
        dx = dx * projectile_speed / magnitude
        dy = dy * projectile_speed / magnitude

        # update self.rotation every tick when we have a target
        angle = math.degrees(math.atan2(dx, dy))
        diff = angle - self.rotation
        mag = abs(diff)

        # correct simple calculation's direction if necessary
        if mag > 180:
            rot = min(self.rotation_speed * dt, 360 - mag)
            diff *= -1
        else:
            rot = min(self.rotation_speed * dt, mag)

        # right, now rotate
        if diff > 0:
            self.rotation += rot
        else:
            self.rotation -= rot

        # and if we're allowed to shoot *and* lined up then BANG!
        diff = int(abs(self.rotation - angle))
        if shoot and diff in (0, 360):
            Bullet(bullet_image, sx, sy, dx=dx, dy=dy, batch=self.game.bullets)
            self.reload = 1

class Bullet(spryte.Sprite):
    time_to_live = 1

    def update(self, dt):
        self.time_to_live -= dt
        if self.time_to_live < 0:
            self.delete()
            return
        x, y = self.position
        x += self.dx * dt
        y += self.dy * dt
        if x < 0 or x > win.width:
            self.delete()
            return
        if y < 0 or y > win.height:
            self.delete()
            return
        self.position = x, y

    def hit(self, enemy):
        enemy.damage(1)

class Enemy(spryte.Sprite):
    health = 10

    def __init__(self, x, y, game, ends):
        self.cell_x, self.cell_y = x, y
        self.game = game
        self.ends = ends

        if self.cell_x == 0:
            x, y = ((self.cell_x-1) * hw + hw//2, self.cell_y * hh + hh//2)
        else:
            x, y = (self.cell_x * hw + hw//2, (self.cell_y+1) * hh + hh//2)
        self.period = .5

        super(Enemy, self).__init__(enemy_image, x, y, batch=game.enemies)

        self.position = (x, y)
        self.move_to(self.cell_x, self.cell_y)

    def damage(self, amount):
        self.health -= amount
        if self.health <=0 :
            self.delete()

    def move_to(self, cx, cy):
        '''Move to the indicated cell.
        '''
        if (cx, cy) in self.ends:
            self.delete()
            return
        self.cell_x, self.cell_y = cx, cy
        x, y = self.cell_x * hw + hw//2, self.cell_y * hh + hh//2
        self.start_x, self.start_y = self.x, self.y
        self.dest_x, self.dest_y = x, y
        self.anim_time = 0
        self.dx = (self.dest_x - self.start_x) / self.period
        self.dy = (self.dest_y - self.start_y) / self.period

    def update(self, dt):
        self.anim_time += dt
        s = (self.anim_time / self.period)
        self.x = self.start_x + s * (self.dest_x - self.start_x)
        self.y = self.start_y + s * (self.dest_y - self.start_y)
        if self.anim_time > self.period:
            self.x = self.dest_x
            self.y = self.dest_y
            self.move_to(*self.game.path.next_step(self.cell_x, self.cell_y))

game = Game()
win.push_handlers(game)
game.spawn_enemies()
clock.schedule(game.update)

# MAIN LOOP
fps = clock.ClockDisplay(color=(1, 1, 1, 1))
while not win.has_exit:
    clock.tick()
    win.dispatch_events()
    win.clear()
    game.draw()
    fps.draw()
    win.flip()

