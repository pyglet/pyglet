import os
import pyglet


window = pyglet.window.Window(width=540, height=540, resizable=True)
print("OpenGL Context: {}".format(window.context.get_info().version))

##########################################################
#   TESTS !
##########################################################
# TODO: update image library to fix this:
# label = pyglet.text.Label("test label")


# vertex_list = pyglet.graphics.vertex_list(3, ('v3f', (-0.6, -0.5, 0,  0.6, -0.5, 0,  0, 0.5, 0)),
#                                              ('c3f', (1, 0, 1, 0, 1, 1, 0, 1, 0)))

batch = pyglet.graphics.Batch()

# batch.add_indexed(4, GL_TRIANGLES, None, [0, 1, 2, 0, 2, 3],
#                   ('v3f', (-0.5, -0.5, 0, 0.5, -0.5, 0, 0.5, 0.5, 0, -0.5, 0.5, 0)),
#                   ('c3f', (1, 0.5, 0.2, 1, 0.5, 0.2, 1, 0.5, 0.2, 1, 0.5, 0.2)),
#                   ('t3f', (0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0)))


# TODO: Add code to send the proper data to the uniform.
os.chdir('..')
img = pyglet.image.load("examples/pyglet.png")
# tex = img.texture
sprite = pyglet.sprite.Sprite(img=img, x=-1, y=-1, batch=batch)


###########################################################
# Set the "zoom" uniform value.
###########################################################
# program.use_program()
# program['zoom'] = 2


##########################################################
# Modify the "zoom" Uniform value scrolling the mouse
##########################################################
# @window.event
# def on_mouse_scroll(x, y, mouse, direction):
#     program.use_program()
#     program['zoom'] += direction / 4
#     if program['zoom'] < 0.1:
#         program['zoom'] = 0.1


###########################################################
# Shader Programs can be used as context managers as shown
# below. You can also manually call the use_program and
# stop_program methods on the Program object, as needed.
###########################################################
@window.event
def on_draw():
    window.clear()
    # pyglet.graphics.draw(3, GL_TRIANGLES, ('v3f', (-0.6, -0.5, 0,  0.6, -0.5, 0,  0, 0.5, 0)),
    #                                       ('c3f', (1, 0.5, 0.2,  1, 0.5, 0.2,  1, 0.5, 0.2)))

    # vertex_list.draw(GL_TRIANGLES)

    # pyglet.graphics.draw_indexed(4, GL_TRIANGLES, [0, 1, 2, 0, 2, 3],
    #                              ('v2i', (-1, -1,   1, -1,   1, 1,   -1, 1)))

    batch.draw()


if __name__ == "__main__":
    pyglet.gl.glClearColor(0.2, 0.3, 0.3, 1)
    pyglet.app.run()
