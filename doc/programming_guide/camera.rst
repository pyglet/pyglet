.. _guide_camera:

Cameras and Views
=================

Pyglet provides camera scopes in :py:mod:`pyglet.window.camera` for 2D and 3D rendering.
For common 2D workflows, use :py:class:`~pyglet.window.camera.Camera2D`. By default, the
window is created with a 2D camera.

What a camera manages
---------------------

A camera describes how world coordinates are projected into a viewport and supplies the resulting
projection and view matrices when drawing. It keeps the transform, viewport, coordinate-conversion,
and shader-data sides of that operation together. This is especially useful when a frame contains
multiple world views, a fixed UI, a minimap, or separate rendering passes.

On modern graphics backends, pyglet supplies camera matrices to shaders through uniform-buffer
storage. Cameras stage matrix changes on the CPU, upload only changed data into ring-buffered GPU
regions, and bind the correct region when a camera draw scope begins. This prevents one camera or
view from accidentally overwriting matrices that the GPU is still using for another draw and avoids
unnecessary synchronization. Applications normally only update camera properties and select which
camera should draw; they do not need to manage this storage directly.

Default camera behavior
-----------------------

Every window has a default camera at :py:attr:`pyglet.window.Window.camera`.
The :py:attr:`~pyglet.window.Window.projection`, :py:attr:`~pyglet.window.Window.view`,
and :py:attr:`~pyglet.window.Window.viewport` properties proxy directly to the
camera's root view.

The default camera is initialized with the window context. A normal ``Batch.draw()`` uses it
automatically unless another camera is selected in the draw options or by a group.

Assigning ``window.projection`` or ``window.view`` remains available for applications that need
custom matrices. Assigning a projection disables the default ``Camera2D`` automatic projection,
so the application is then responsible for updating that matrix when the window or viewport changes.

Creating 2D and 3D cameras
--------------------------

Create cameras from a window, and optionally configure scroll/zoom behavior::

    window = pyglet.window.Window()

    world_camera = pyglet.window.camera.Camera2D(
        window,
        scroll_speed=5,
        min_zoom=0.25,
        max_zoom=4,
    )

    world_camera.zoom += 0.25
    world_camera.move(1, 0)
    world_camera.position = (50, 0)

For perspective rendering, create a :py:class:`~pyglet.window.camera.Camera3D`::

    from pyglet.math import Vec3
    from pyglet.window.camera import Camera3D

    scene_camera = Camera3D(
        window,
        position=Vec3(0, 2, 8),
        target=Vec3(0, 1, 0),
        near=0.1,
        far=1000.0,
        field_of_view=60.0,
    )

Use :py:class:`~pyglet.window.camera.FPSCamera` for first-person movement or
:py:class:`~pyglet.window.camera.ThirdPersonCamera` for an orbiting camera that follows a target.
These are presets built on ``Camera3D`` and use the same drawing and view APIs.

Multiple cameras and views
--------------------------

An application can create any number of 2D and 3D camera instances. Each camera has independent
projection settings and managed matrix storage, so separate world, UI, player, and render-pass
cameras do not conflict with one another.

A camera *view* is useful when several draw scopes belong to the same camera. Views share their
camera's projection behavior while providing their own transform, viewport, scissor, and matrix
storage. They can inherit transforms from other views, making them a lighter and more closely related
alternative to creating another independent camera.


Creating views
--------------

A camera can have multiple views. Views let you scope additional transforms and scissor
areas inside one camera.

Use ``camera.create_view()`` for additional view scopes. This is useful for parallax
layers, minimaps, and nested local transforms::

    window = pyglet.window.Window()

    ui_camera = pyglet.window.camera.Camera2D(window)
    inherited_view = ui_camera.create_view(inherit=True)      # Inherits parent transform chain.
    independent_view = ui_camera.create_view(inherit=False)   # Parented to camera root view.

Views share the camera's projection behavior and can be used anywhere a camera
scope is expected. Each view has its own viewport, inherited from its parent view
unless explicitly overridden.

Views can also be created from other views. For example::

    ui_camera = pyglet.window.camera.Camera2D(window)
    scroll_box_a = ui_camera.create_view()
    scroll_box_b = scroll_box_a.create_view()

If ``scroll_box_a`` moves or zooms, ``scroll_box_b`` inherits those changes.

Using camera scopes with batches
--------------------------------

Cameras can be used to target a specific batch instead of groups::

    @window.event
    def on_draw():
        window.clear()

        with world_batch.draw_with_options() as options:
            options.camera = world_camera

        with gui_batch.draw_with_options() as options:
            options.camera = gui_camera


Using camera scopes in groups
-----------------------------

Attach camera scopes to groups with ``Group.set_camera``::

    world_group = pyglet.graphics.Group(order=0)
    world_group.set_camera(world_camera)

    ui_group = pyglet.graphics.Group(order=1)
    ui_group.set_camera(window.camera)

    pyglet.sprite.Sprite(world_image, batch=batch, group=world_group)
    pyglet.text.Label("HUD", batch=batch, group=ui_group)


.. note:: ``Group.set_camera`` applies camera state at draw entry by calling ``begin()``.
          It does not call ``end()`` during group unsetting.

When camera changes are applied
-------------------------------

Changing ``position``, ``zoom``, orientation, projection, or viewport updates camera state, but it
does not immediately replace the matrices used by unrelated drawing. The matrices are resolved,
committed, and bound when the camera's batch or group scope begins. Make camera changes before the
draw that should use them::

    def update(dt):
        world_camera.move(input_x * dt, input_y * dt)

    @window.event
    def on_draw():
        window.clear()
        with world_batch.draw_with_options() as options:
            options.camera = world_camera

Applications normally should not call ``camera.begin()`` or ``camera.end()`` directly. Batch draw
options and camera groups provide the rendering context needed to apply the state correctly.

Custom shader integration
-------------------------

Custom vertex shaders on modern graphics backends can consume the selected camera through the same
``WindowBlock`` used by pyglet's built-in shaders::

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
        gl_Position = window.projection * window.view * vec4(position, 1.0);
    }

pyglet assigns the ``WindowBlock`` binding and binds the selected camera's region for each camera
scope. Multiple ``Camera2D``, ``Camera3D``, and camera-view instances are supported; each receives
managed storage. Avoid manually uploading or replacing the ``WindowBlock`` data used by these
camera-scoped draws, because doing so bypasses the per-camera regions and draw-time binding.

OpenGL 2 and OpenGL ES 2 shaders
---------------------------------

The OpenGL 2 and OpenGL ES 2 backends do not use uniform buffers. On these backends, a camera writes
ordinary ``u_projection`` and ``u_view`` uniforms to the active shader program::

    uniform mat4 u_projection;
    uniform mat4 u_view;

    void main()
    {
        gl_Position = u_projection * u_view * vec4(position, 1.0);
    }

If a custom shader uses different names, pass them as ``projection_uniform`` and ``view_uniform``
when constructing the camera. Camera movement, views, batches, and groups otherwise use the same API.

Viewport
--------

Each camera view has a ``viewport`` in framebuffer coordinates::

    world_camera.viewport = (0, 0, window.width // 2, window.height)

``camera.viewport`` remains as a convenience proxy for ``camera.view.viewport``.
Set ``view.viewport`` directly when a child view needs a different viewport::

    minimap_view = world_camera.create_view()
    minimap_view.viewport = (16, 16, 256, 256)

Viewport belongs to the view because the viewport determines how that specific
view maps drawn content into framebuffer pixels. Child views can represent split
screens, minimaps, editor panels, or nested render regions while still sharing
the same camera projection and storage behavior.

By default, the root view's viewport follows the full framebuffer and updates on
resize/scale events. A child view inherits its parent viewport until it is given
an explicit value. Setting a tuple makes that view's viewport explicit, and it
will no longer update automatically. In those cases you will have to update your
viewport coordinates explicitly.

Coordinate conversion
---------------------

Cameras and views provide helpers for moving points through the same coordinate
spaces used when drawing::

    @window.event
    def on_mouse_press(x, y, button, modifiers):
        world_position = world_camera.screen_to_world(x, y)
        minimap_position = minimap_view.screen_to_world(x, y)

Use the camera methods for the root view, or call the same methods on a child
view when viewport inheritance or view-local transforms matter. The helpers
include conversions between screen, viewport, view, and world spaces, such as
``screen_to_viewport``, ``viewport_to_world``, ``screen_to_world``, and
``world_to_screen``.

Scissor
-------

Scissor clipping can be set on both cameras and views.

Use ``set_scissor_area(...)`` for fixed window-space clipping::

    world_camera.set_scissor_area(0, 0, window.width // 2, window.height)

Use ``set_scissor_area_relative(...)`` when clipping should move with the
camera/view transform::

    moving_panel = ui_camera.create_view(inherit=True)
    moving_panel.set_scissor_area_relative(40, 40, 280, 160)
    moving_panel.offset_x += 16   # Scissor follows the moved view

When a camera/view is applied through ``Group.set_camera``, pyglet automatically applies
matching scissor state for that group.

For nested views, the effective scissor is the intersection of all scissor areas in the
view chain.
