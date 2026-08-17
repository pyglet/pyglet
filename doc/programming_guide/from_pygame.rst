.. _guide_from_pygame:

From pygame to pyglet
=====================

This page is for migrating an existing pygame project to pyglet.
It focuses on API patterns that are similar in intent but different in usage.

The main model shift centered around pygame going into pyglet will be the following concepts:

* Polling events every frame
* Blitting ``pygame.Surface`` objects into a display surface
* Flipping the display at the end of each frame

pyglet code is usually organized around:

* Registering event handlers
* Drawing sprites (textures) in ``on_draw``
* Letting :py:func:`pyglet.app.run` drive input and redraw timing
* Creating draw objects once, then reusing them each frame

Benefits to switching
---------------------

The most common reasons for switching to pyglet over pygame are the following:

* Better scaling for many on-screen objects through batching.
* Cleaner separation between update logic and draw logic.
* A more explicit event model (key/mouse/window callbacks).
* Built-in scheduling tools for periodic and delayed tasks.
* APIs that map well to object-oriented game structure.
* Utilizing graphics shaders for advanced effects.

Coordinate system
-----------------
The first major difference will be the coordinate system. OpenGL (the default pyglet
graphics backend) utilizes a bottom left origin point (0,0). This is based off the Cartesian
coordinate system, where positive Y-axis increases upwards. Think of your window as a graph, with
the bottom left corner being the (0,0) position. Left is negative on the X axis, while down is
negative on the Y axis.

In pygame 0,0 is a top left origin point, commonly called a screen coordinate system. (0,0) begins
at the top left and increasing the Y position moves it from top to bottom.

Event loop: polling vs event-driven
-----------------------------------

Another difference will be regarding the event loop, in pygame
you may have a loop like the following:

.. code-block:: python

    import pygame

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # update game state here
        screen.fill((25, 25, 25))
        # screen.blit(...)
        pygame.display.flip()

In pygame, you explicitly poll events each loop/frame, and create conditional statements to handle those
portions of code.

With pyglet, the event loop is managed for you behind the scenes, dispatching events from each Window
when it occurs.

A function (or multiple) can then be registered to these callbacks allowing code to be separated
into more readable chunks. For a complete listing of Window events, check out the documentation and
examples.

.. code-block:: python

    import pyglet

    window = pyglet.window.Window(800, 600, caption="My Game")

    def update(dt):
        # update game state here
        pass

    @window.event
    def on_draw():
        window.clear()
        # draw objects here

    pyglet.clock.schedule_interval(update, 1 / 60)
    pyglet.app.run()



Input handling
--------------

In pygame, input handling is usually split between:

* Event polling for discrete events (``KEYDOWN``, ``MOUSEBUTTONUP``, etc).
* State queries like ``pygame.key.get_pressed()`` for continuous movement.

In pyglet, the primary model are event handlers on the window. Typical handlers are:

* ``on_key_press`` / ``on_key_release``
* ``on_mouse_press`` / ``on_mouse_release``
* ``on_mouse_drag`` / ``on_mouse_motion``

pygame (event polling):

.. code-block:: python

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            player.jump()
        elif event.type == pygame.MOUSEBUTTONUP:
            handle_click(event.pos)

Pyglet example:

.. code-block:: python

    import pyglet
    from pyglet.window import key, mouse

    @window.event
    def on_key_press(symbol, modifiers):
        if symbol == key.SPACE:
            player.jump()

    @window.event
    def on_mouse_release(x, y, button, modifiers):
        if button == mouse.LEFT:
            handle_click((x, y))

    @window.event
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        if buttons & mouse.LEFT:
            drag_selection(dx, dy)

For continuous movement, pyglet still supports state-style input with
``KeyStateHandler`` and ``MouseStateHandler``:

For pygame, it would look like this:

.. code-block:: python

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_x -= speed

With pyglet's event style, you would register the KeyStateHandler object (``keys``) as an instance that
can handle events for the window:

.. code-block:: python

    keys = pyglet.window.key.KeyStateHandler()
    window.push_handlers(keys)  # Registers the object that receives window event.

    def update(dt):
        if keys[pyglet.window.key.LEFT]:
            player_x -= speed * dt

Use event callbacks for discrete actions, and state handlers for continuous actions.

Clock and scheduling
--------------------

pygame commonly uses ``clock.tick(fps)`` and manual timers in the main loop:

.. code-block:: python

    clock = pygame.time.Clock()
    spawn_timer = 0.0

    while running:
        dt = clock.tick(60) / 1000.0
        spawn_timer += dt
        if spawn_timer >= 2.0:
            spawn_enemy()
            spawn_timer = 0.0

pyglet gives direct scheduling functions without manual timer bookkeeping:

.. code-block:: python

    def update(dt):
        simulate_world(dt)

    def spawn_enemy(dt):
        make_enemy()

    def player_spawn(dt):
        spawn_player()

    pyglet.clock.schedule_interval(update, 1 / 60)
    pyglet.clock.schedule_interval(spawn_enemy, 2.0)
    pyglet.clock.schedule_once(spawn_player, 0.5)
    pyglet.app.run()

You can also schedule one time events via ``clock.schedule_once``.

.. tip:: You can also set the timing precision of the app loop by passing a value into
         ``pyglet.app.run(1 / 60.0)``. By default this is 1 / 60.0. Lowering the value may improve timing
         resolution on some systems at the cost of CPU usage. You can set to 0.0 for as fast as possible.


Surfaces vs images and textures
-------------------------------

Pygame's main rendering focus is surface-centric. Which is decoding image data into
a ``pygame.Surface``, which then blits those surfaces into the display surface.
That path is often a CPU operation in traditional SDL surface workflows. While this gives
great compatibility, it often ignores the most powerful part of the computer that is made
to handle these tasks: the GPU.

pyglet separates these concepts into CPU image data from GPU textures more explicitly:

* :py:func:`pyglet.image.load` and :py:func:`pyglet.resource.image` returns CPU-side image data:
:py:class:`pyglet.image.ImageData`. This is a container of information on the image, including the
format, size, and bytes that make up that data. This data by itself cannot do anything, it needs to be
uploaded to the GPU for use in drawing.
* :py:func:`pyglet.resource.texture` returns a GPU texture suitable for drawing. This loads the
ImageData and uploads the texture for you behind the scenes.

There are various ways to display a texture, but the most common will be a ``pyglet.sprite.Sprite``.
It is a high-level object that has many different properties and functions that can be used to modify
how it is displayed.

pygame:

.. code-block:: python

    player_surface = pygame.image.load("player.png").convert_alpha()
    screen.blit(player_surface, (x, y))

In pyglet, after setting your path, load the texture and pass it to the sprite.

.. code-block:: python

    pyglet.resource.path = ["assets"]
    pyglet.resource.reindex()

    player_texture = pyglet.resource.texture("player.png")
    player_sprite = pyglet.sprite.Sprite(player_texture, x=x, y=y)

    @window.event
    def on_draw():
        window.clear()
        player_sprite.draw()

You can then modify the ``player_sprite`` properties to adjust things such as scale, colors, and more.

.. note::
   pygame can also use accelerated paths (for example with OpenGL or SDL renderer),
   but many existing projects are built around software-style surface blitting.

Transparency and image loading
------------------------------

In pygame, when loading images, you often need to decide between:

* ``convert()``: Fast, but no alpha.
* ``convert_alpha()``: To preserve alpha.
* Implementing color-key transparency.

Typical pygame examples often include color-key management:

.. code-block:: python

    surf = pygame.image.load("enemy.bmp").convert()
    surf.set_colorkey((255, 0, 255))

In pyglet, PNG alpha is naturally preserved in textures, so transparent assets
generally work without extra color-key steps:

.. code-block:: python

    enemy_tex = pyglet.resource.texture("enemy.png")  # alpha kept
    enemy = pyglet.sprite.Sprite(enemy_tex, x=100, y=80)

The default blend mode for objects like Sprites are how you might expect a scene to behave.

Blitting vs drawing and batching
--------------------------------

In pygame, it is normal to blit many surfaces each frame. In graphics programming, it can be very
poor performing to draw each object one by one. While useful for initial setup or debugging, it is
usually better to draw many objects through one ``pyglet.graphics.Batch``. This class will group
many objects with the same state into one single draw call, letting you render thousands of
objects with very little performance impact.

Here is an example of how you might have rendered via pygame:

.. code-block:: python

    for enemy in enemies:
        screen.blit(enemy.surface, enemy.pos)

And with pyglet batching:

.. code-block:: python

    batch = pyglet.graphics.Batch()
    enemy_sprites = [
        pyglet.sprite.Sprite(enemy_tex, x=e.x, y=e.y, batch=batch)
        for e in enemies
    ]

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

Batching reduces draw overhead and generally scales better as object count grows.

Geometry lifetime: recreate every frame vs reuse
------------------------------------------------

A common pygame pattern is building draw geometry in the loop, for example:

.. code-block:: python

    # every frame
    pygame.draw.rect(screen, (255, 0, 0), (x, y, w, h))

This is simple and valid, but it keeps most draw setup tied to the frame loop.

In pyglet, a common pattern is to create draw objects once, then only update
their properties:

.. code-block:: python

    batch = pyglet.graphics.Batch()
    hp_bar = pyglet.shapes.Rectangle(x, y, w, h, color=(255, 0, 0), batch=batch)

    def update(dt):
        hp_bar.width = current_hp_width

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

This typically reduces per-frame object churn and lets pyglet keep geometry in
GPU-friendly structures. Otherwise, you would essentially be creating the geometry, uploading it,
then throwing away, and repeating each frame.

.. tip:: Avoid creating any objects in any scheduled functions or draws. You want to create an object
         once and re-use it where possible. Even in cases like sprites, you can set a sprite visible property
         to ``False``, and then re-use it later by attaching a new texture to it and making it visible again.

Collision and ``Rect`` migration
--------------------------------

pygame code often relies on ``pygame.Rect`` and helpers like ``colliderect``.
pyglet intentionally does not force one built-in collision primitive for all
projects, so there is no direct single ``pyglet.Rect`` replacement in the
high-level API.

For straightforward 2D collisions, simple AABB checks are usually enough:

.. code-block:: python

    def aabb_overlap(a, b):
        return (
            a.left < b.right and a.right > b.left and
            a.bottom < b.top and a.top > b.bottom
        )

For more advanced collision/physics, use a dedicated library such as ``pymunk``.

Minimal migration checklist
---------------------------

1. Replace the manual ``while running`` loop with ``pyglet.app.run()``.
2. Move rendering into ``on_draw``.
3. Move simulation into scheduled update functions (for example, 60 Hz).
4. Replace ``Surface`` + ``blit`` patterns with ``Texture`` + ``Sprite``.
5. Group many drawables into a ``pyglet.graphics.Batch``.
6. Replace polled input where useful with pyglet event handlers.
7. Convert ``Rect``-centric collision code to AABB helpers or a physics library.
8. Prefer creating draw objects once, then mutating state instead of recreating.

Next reading:

* :doc:`eventloop`
* :doc:`events`
* :doc:`image`
* :doc:`texture`
* :doc:`rendering`
