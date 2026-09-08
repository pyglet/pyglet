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

Textures created from pyglet images are not limited to ``RGBA``. The upload
path retains directly supported component orders, including ``RGB`` and
``RGBA``, and converts source data to a compatible order when necessary. In
particular, ``BGR`` and ``BGRA`` data is uploaded directly only when the GLES
implementation advertises a BGRA texture-format extension; otherwise pyglet
converts it to ``RGB`` or ``RGBA`` before the upload. Legacy ``L`` and ``LA``
images are represented with red and red/green components and texture swizzles.

OpenGL ES does not perform arbitrary component-order conversion as part of
``glTexImage`` or ``glTexSubImage``. The external pixel format must be
compatible with the texture's storage format. Pyglet therefore chooses a
compatible external format and performs any required conversion on the CPU.
Applications using the GL bindings directly must make the same choice and
should check for a BGRA extension before using ``GL_BGRA``.

When an image decoder can select its output format, pyglet normally requests
``RGBA`` for OpenGL ES contexts. The exception is Windows, where pyglet may
prefer ``BGRA`` when the active context supports direct BGRA uploads. This
matches the native Windows decoder format and avoids a CPU conversion. Decoders
are not required to produce the preferred format.

Compute Shader
~~~~~~~~~~~~~~

Textures used as image units in a compute shader require immutable storage on
OpenGL ES 3.1. Create them with ``immutable=True``::

    from pyglet.enums import ComponentFormat
    from pyglet.graphics import Texture

    texture = Texture.create(
        512,
        512,
        internal_format=ComponentFormat.RGBA,
        internal_format_size=32,
        internal_format_type="f",
        blank_data=False,
        immutable=True,
    )

The texture's dimensions, internal format, and number of mipmap levels are
then fixed. You can still upload and update its pixel data normally. The
texture format must match the image format declared in the shader.

For GLSL ES 3.10, image formats other than ``r32f``, ``r32i``, and ``r32ui``
also need an access qualifier. An ``rgba32f`` output image is typically
declared as::

    layout(rgba32f) writeonly uniform highp image2D output_image;

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
