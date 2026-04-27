import math

import pytest

import pyglet
from pyglet import clock, window
from pyglet.enums import GeometryMode
from pyglet.graphics.api.gl import gl
from pyglet.window import key

from tests.base.interactive import InteractiveTestCase


@pytest.mark.requires_user_action
class WINDOW_MULTISAMPLE(InteractiveTestCase):
    """Test that a window can have multisample.

    A window will be opened containing two rotating squares. Initially,
    there will be no multisampling (the edges will look "jaggy"). Press:

        * M to toggle multisampling on/off
        * S to increase samples (2, 4, 6, 8, 10, ...)
        * Shift+S to decrease samples
        * N to enable/disable GL_MULTISAMPLE
        * P to pause/resume square rotation

    Each time sample_buffers or samples is modified, the window will be recreated.
    Watch the console for success and failure messages. If the multisample
    options are not supported, a "Failure" message will be printed and the window
    will be left as-is.

    Press ESC to end the test.
    """
    win = None
    width = 640
    height = 480

    soft_multisample = True
    multisample = False
    samples = 2
    spin_enabled = True

    program = None
    scene_batch = None
    red_square = None
    green_square = None

    def set_window(self):
        oldwindow = self.win
        old_red_square = self.red_square
        old_green_square = self.green_square

        new_window = None
        try:
            config = pyglet.config.Config()
            backend_config = getattr(config, pyglet.options.backend)
            backend_config.double_buffer = True
            if self.multisample:
                print('Attempting samples=%d...' % self.samples, end=' ')
                backend_config.sample_buffers = 1
                backend_config.samples = self.samples
            else:
                print('Disabling multisample...', end=' ')
                backend_config.sample_buffers = 0
                backend_config.samples = 0

            new_window = window.Window(self.width, self.height,
                                       vsync=True,
                                       config=config)
            new_window.switch_to()
            new_window.push_handlers(self.on_key_press)
            new_window.context.set_clear_color(0.0, 0.0, 0.0, 1.0)

            if self.soft_multisample:
                gl.glEnable(gl.GL_MULTISAMPLE)
            else:
                gl.glDisable(gl.GL_MULTISAMPLE)

            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

            program = pyglet.graphics.get_default_shader()
            scene_batch = pyglet.graphics.Batch()

            red_square = program.vertex_list(
                6,
                GeometryMode.TRIANGLES,
                batch=scene_batch,
                position=('f', (0.0,) * 18),
                colors=('f', (1.0, 0.0, 0.0, 1.0) * 6),
            )
            green_square = program.vertex_list(
                6,
                GeometryMode.TRIANGLES,
                batch=scene_batch,
                position=('f', (0.0,) * 18),
                colors=('f', (0.0, 1.0, 0.0, 0.5) * 6),
            )

            self.win = new_window
            self.program = program
            self.scene_batch = scene_batch
            self.red_square = red_square
            self.green_square = green_square
            if not hasattr(self, 'angle'):
                self.angle = 0.0
            self._update_geometry()
            new_window.dispatch_events()

            if oldwindow:
                oldwindow.switch_to()
                self._delete_render_resources(old_red_square, old_green_square)
                oldwindow.close()

            print('Actual config: sample_buffers=%s, samples=%s'
                  % (getattr(new_window.config, 'sample_buffers', None),
                     getattr(new_window.config, 'samples', None)))
            print('Success.')
        except window.NoSuchConfigException:
            print('Failed.')
        except Exception:
            if new_window is not None:
                new_window.close()
            raise

    @staticmethod
    def _delete_render_resources(red_square, green_square):
        if red_square is not None:
            red_square.delete()
        if green_square is not None:
            green_square.delete()

    def _build_quad_vertices(self, angle, size):
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        center_x = self.width / 2
        center_y = self.height / 2
        points = (
            (-size, -size),
            (size, -size),
            (size, size),
            (-size, -size),
            (size, size),
            (-size, size),
        )
        vertices = []
        for x, y in points:
            rx = x * cos_a - y * sin_a + center_x
            ry = x * sin_a + y * cos_a + center_y
            vertices.extend((rx, ry, 0.0))
        return tuple(vertices)

    def _update_geometry(self):
        size = self.height / 4
        self.red_square.position[:] = self._build_quad_vertices(self.angle, size)
        self.green_square.position[:] = self._build_quad_vertices(-self.angle * 2, size)

    def on_key_press(self, symbol, modifiers):
        mod = 1
        if modifiers & key.MOD_SHIFT:
            mod = -1

        if symbol == key.M:
            self.multisample = not self.multisample
            self.set_window()
        if symbol == key.S:
            self.samples += 2 * mod
            self.samples = max(2, self.samples)
            self.set_window()

        if symbol == key.P:
            self.spin_enabled = not self.spin_enabled
            if self.spin_enabled:
                print('Resuming rotation.')
            else:
                print('Pausing rotation.')

        # Additional test: toggle GL_MULTISAMPLE state.
        if symbol == key.N:
            self.soft_multisample = not self.soft_multisample
            if self.soft_multisample:
                print('Enabling GL_MULTISAMPLE')
                gl.glEnable(gl.GL_MULTISAMPLE)
            else:
                print('Disabling GL_MULTISAMPLE')
                gl.glDisable(gl.GL_MULTISAMPLE)

    def render(self):
        self.win.switch_to()
        self._update_geometry()
        self.win.clear()
        self.scene_batch.draw()

    def test_multisample(self):
        self.set_window()
        try:
            self.angle = 0.0
            while not self.win.has_exit:
                dt = clock.tick()
                if self.spin_enabled:
                    self.angle += dt

                self.render()
                self.win.flip()
                self.win.dispatch_events()
        finally:
            if self.win is not None:
                self.win.switch_to()
                self._delete_render_resources(self.red_square, self.green_square)
                self.win.close()
                self.win = None
                self.program = None
                self.scene_batch = None
                self.red_square = None
                self.green_square = None
        self.user_verify('Pass test?', take_screenshot=False)
