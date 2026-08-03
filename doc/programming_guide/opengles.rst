.. _programming-guide-opengles:


OpenGL ES
=========

Pyglet has experimental support for OpenGL ES 3.0, 3.1, and 3.2, with some limitations. OpenGL ES 3.1 or
higher is recommended. Devices such as
Raspberry Pi 4 and 5 commonly expose OpenGL ES 3.1, often with extensions covering portions of ES 3.2.

.. tip::

   Use the :ref:`pyglet-info` graphics probe on the target machine before
   choosing a context version. It verifies candidate configurations and
   reports a recommended request.

Creating a window / context
---------------------------

In order to successfully create a context and window with OpenGL ES we first need to:

* Select an OpenGL ES backend
* Pass in a custom config at window creation specifying ES version
  
Example::

    import pyglet

    # Select OpenGL ES backend:
    pyglet.options.backend = "gles3"

    # Raspberry Pi 4 and 5 commonly use OpenGL ES 3.1.
    config = pyglet.config.Config()
    config.gles3.major_version = 3
    config.gles3.minor_version = 1

    # Create the window
    window = pyglet.window.Window(config=config)


Limitations
-----------

Multisampling
~~~~~~~~~~~~~

Be careful with enabling multisampling on the window. Likely 
the default configuration will not have multisampling enabled.

Textures
~~~~~~~~

Pixel format for textures and images are limited to ``RGBA``. If you try to
load any other pixel format through pyglet's image loading functions you
will get an error when they are turned into OpenGL textures later.

The reason for this limitation is that OpenGL ES does not support pixel
format conversion during pixel transfer, meaning when calling ``glTexImage``
to upload pixel data to the GPU, the pixel format must match the internalformat.
In desktop OpenGL an RGB image will be automatically converted to RGBA during
this transfer. This is not supported in OpenGL ES.

You are, however, free to create your own textures with any pixel format
using the gl bindings directly.

Compute Shader
~~~~~~~~~~~~~~

If you are planning to bind textures to image units with the intention of
using them in a compute shader, you need to create these textures yourself
using the gl bindings and allocate space using ``glTexStorage``. Pyglet is
using ``glTexImage`` to allocate space and upload the pixel data for textures.

The difference here is that ``glTexStorage`` creates immutable storage. You can
only call it once and then fill the allocated space with pixel data using
``glTexSubImage``. ``glTexImage`` on the other hand can be called multiple times
reallocating the texture storage each time. Likely OpenGL ES doesn't want to
deal with the extra complexity of validating the texture storage of images
every time a compute shader is dispatched.

In short: Create your own textures with immutable storage if you are planning
to use them in a compute shader.

Shaders
-------

Pyglet's shader system supports basic conversion between GLSL 1.5/3.3 shaders
and GLES shaders when running in OpenGL ES mode. Built-in shaders are converted
to GLSL ES 3.00 on GLES 3.0 and GLSL ES 3.10 on GLES 3.1 or newer. Precision
qualifiers are injected using ``mediump`` by default.

Use ``window.context.info.features`` for functionality that is not guaranteed
by every supported ES version. For example, compute shaders and shader-storage
buffers require GLES 3.1 (or a supported desktop equivalent)::

    features = window.context.info.features
    if features.compute_shaders and features.shader_storage_buffers:
        # Safe to create pyglet ComputeShaderProgram objects.
        pass
