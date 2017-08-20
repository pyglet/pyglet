import os
import pyglet
from pyglet.gl import *


# pyglet.options['debug_gl_shaders'] = True

window = pyglet.window.Window(width=540, height=540, resizable=True)
print("OpenGL Context: {}".format(window.context.get_info().version))

##########################################################
#   TESTS !
##########################################################
# TODO: update text module to fix this:
# label = pyglet.text.Label("test label")


vertex_list = pyglet.graphics.vertex_list(3, ('v3f', (-0.6, -0.5, 0,  0.6, -0.5, 0,  0, 0.5, 0)),
                                             ('c3f', (1, 0, 1, 0, 1, 1, 0, 1, 0)))

batch = pyglet.graphics.Batch()


def create_quad_vertex_list(x, y, z, width, height):
    return x, y, z, x + width, y, z, x + width, y + height, z, x, y + height, z


batch.add_indexed(4, GL_TRIANGLES, None, [0, 1, 2, 0, 2, 3],
                  ('v3f', create_quad_vertex_list(200, 200, 0, 55, 55)),
                  ('c3f', (1, 0.5, 0.2, 1, 0.5, 0.2, 1, 0.5, 0.2, 1, 0.5, 0.2)),
                  ('t2f', (0, 0,  1, 0,  1, 1,  0, 1)))

batch.add_indexed(4, GL_TRIANGLES, None, [0, 1, 2, 0, 2, 3],
                  ('v2f', (40, 40, 40+50, 40, 40+50, 40+50, 40, 40+50)),
                  ('c3f', (1, 0.5, 0.2, 1, 0.5, 0.2, 1, 0.5, 0.2, 1, 0.5, 0.2)))


# TODO: Add code to send the proper data to the uniform.
os.chdir('..')
img = pyglet.image.load("examples/pyglet.png")
sprite = pyglet.sprite.Sprite(img=img, x=10, y=10, batch=batch)
sprite2 = pyglet.sprite.Sprite(img=img, x=200, y=200, batch=batch)
sprite3 = pyglet.sprite.Sprite(img=img, x=300, y=100, batch=batch)
# sprite4 = pyglet.sprite.Sprite(img=img, x=300, y=200, batch=batch)
# sprite5 = pyglet.sprite.Sprite(img=img, x=300, y=300, batch=batch)


###########################################################
# Set the "zoom" uniform value.
###########################################################
program = pyglet.graphics.default_group.shader_program
program.use_program()
program['window_size'] = window.width, window.height

print("zoom", program['zoom'])
print("size", program['window_size'])
print("texture loc", program['our_texture'])


##########################################################
# Modify the "zoom" Uniform value scrolling the mouse
##########################################################
@window.event
def on_mouse_scroll(x, y, mouse, direction):
    if not program.active:
        program.use_program()
    program['zoom'] += direction / 32
    if program['zoom'] < 0.1:
        program['zoom'] = 0.1


###########################################################
#
###########################################################
@window.event
def on_draw():
    window.clear()
    # pyglet.graphics.draw(3, GL_TRIANGLES, ('v3f', (-0.6, -0.5, 0,  0.6, -0.5, 0,  0, 0.5, 0)),
    #                                       ('c3f', (1, 0.5, 0.2,  1, 0.5, 0.2,  1, 0.5, 0.2)))
    # TODO: fix drawing vertex_lists
    # vertex_list.draw(GL_TRIANGLES)

    # pyglet.graphics.draw_indexed(4, GL_TRIANGLES, [0, 1, 2, 0, 2, 3],
    #                              ('v2i', (-1, -1,   1, -1,   1, 1,   -1, 1)),
    #                              ('c3f', (1, 0.5, 0.2,  1, 0.5, 0.2,  1, 0.5, 0.2, 1, 0.5, 0.2)))

    # glActiveTexture(GL_TEXTURE0)
    # glBindTexture(img.texture.target, img.texture.id)

    batch.draw()


if __name__ == "__main__":
    pyglet.gl.glClearColor(0.2, 0.3, 0.3, 1)
    pyglet.app.run()
