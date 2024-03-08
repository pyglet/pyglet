import pyglet


class Scene:

    manager: "SceneManager"

    def set_scene(self, scene_name):
        self.manager.set_scene(scene_name)

    def activate(self):
        pass

    def deactivate(self):
        pass

    def draw(self):
        pass

    def update_scene(self, dt):
        pass

    # Controller event handlers:

    def on_dpad_motion(self, controller, vector):
        pass

    def on_stick_motion(self, controller, name, vector):
        pass

    def on_trigger_motion(self, controller, value):
        pass

    def on_button_press(self, controller, button):
        pass

    def on_button_release(self, controller, button):
        pass

    # Keyboard event handlers:

    def on_key_press(self, symbol, modifiers):
        pass

    def on_key_release(self, symbol, modifiers):
        pass


class SceneManager:

    def __init__(self, window):
        self.window = window
        self.window.on_draw = self._on_draw

        self._scenes = {}
        self.current_scene = None

        # Instantiation a ControllerManager to handle hot-plugging:
        self.controller = None
        self.controller_manager = pyglet.input.ControllerManager()
        self.controller_manager.on_connect = self.on_controller_connect
        self.controller_manager.on_disconnect = self.on_controller_disconnect

        # Initialize Controller if it's connected:
        controllers = self.controller_manager.get_controllers()
        if controllers:
            self.on_controller_connect(controllers[0])

    def _on_draw(self):
        self.window.clear()
        self.current_scene.draw()

    def on_controller_connect(self, controller):
        if not self.controller:
            controller.open()
            self.controller = controller
            self.controller.push_handlers(self.current_scene)
        else:
            print(f"A Controller is already connected: {self.controller}")

    def on_controller_disconnect(self, controller):
        if self.controller == controller:
            self.controller.remove_handlers(self.current_scene)
            self.controller = None

    def add_scene(self, scene_class, *args, alias=None):
        scene_class.manager = self
        name = alias or scene_class.__name__

        scene_instance = scene_class(*args)

        self._scenes[name] = scene_instance
        self.current_scene = scene_instance
        self.window.clear()

    def set_scene(self, scene):
        assert scene in self._scenes, "Scene not found! Did you add it?"

        if self.current_scene:
            self.current_scene.deactivate()
            self.window.remove_handlers(self.current_scene)
            if self.controller:
                self.controller.remove_handlers(self.current_scene)

        self.current_scene = self._scenes[scene]
        self.current_scene.activate()
        self.window.push_handlers(self.current_scene)
        if self.controller:
            self.controller.push_handlers(self.current_scene)

    def update(self, dt):
        self.current_scene.update_scene(dt)
