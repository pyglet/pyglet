import pyglet

from pyglet.math import Mat4, Vec3, Quaternion

window = pyglet.window.Window(resizable=True)
batch = pyglet.graphics.Batch()
camera = pyglet.window.camera.FPSCamera(window, position=Vec3(0.0, 0.0, 5.0), target=Vec3(0.0, 0.0, 0.0))


@window.event
def on_draw():
    window.clear()
    # Set the camera explicity while drawing the Batch:
    with batch.draw_with_options() as options:
        options.camera = camera


def animate(dt):
    animate.elapsed += dt

    rot_x = Quaternion.from_rotation(animate.elapsed/1, Vec3(1, 0, 0))
    rot_y = Quaternion.from_rotation(animate.elapsed/2, Vec3(0, 1, 0))
    rot_z = Quaternion.from_rotation(animate.elapsed/3, Vec3(0, 0, 1))
    model_logo_instance.rotation = rot_x @ rot_y @ rot_z

    rot_x = Quaternion.from_rotation(animate.elapsed/1, Vec3(1, 0, 0))
    rot_y = Quaternion.from_rotation(animate.elapsed/2, Vec3(0, 1, 0))
    rot_z = Quaternion.from_rotation(animate.elapsed/3, Vec3(0, 0, 1))
    model_box_instance.rotation = rot_x @ rot_y @ rot_z


if __name__ == "__main__":
    logo_scene = pyglet.resource.scene('logo3d.obj')
    box_scene = pyglet.resource.scene('box.obj')

    model_logo = logo_scene.create_models(batch=batch)[0]   # only one model in this scene
    model_logo_instance = model_logo.create_instance(translation=Vec3(1.25, 0.0, 1.0))

    model_box = box_scene.create_models(batch=batch)[0]     # only one model in this scene
    model_box_instance = model_box.create_instance(translation=Vec3(-1.25, 0.0, 0.0))

    animate.elapsed = 0.0
    pyglet.clock.schedule_interval(animate, 1 / 60)
    pyglet.app.run()
