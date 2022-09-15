Installation
============

.. note:: These instructions apply to pyglet |version|.

pyglet is a pure python library, so no special steps or complitation are
required for installation. You can install it in a variety of ways, or simply
copy the `pyglet` folder directly into your project. If you're unsure what to do,
the recommended method is to install it into your local ``site-packages``
directory. pyglet is available `on PyPI <https://pypi.python.org/pypi/pyglet>`_.
for easy installation via **pip**:

.. code-block:: sh

    pip install pyglet --user

You can also clone the repository using **git** and install from source:

.. code-block:: sh

    git clone https://github.com/pyglet/pyglet.git
    cd pyglet
    git checkout pyglet-1.5-maintenance
    python setup.py install --user


To play video, or a wide selection of compressed audio, pyglet can optionally
use `FFmpeg <https://www.ffmpeg.org/download.html>`_.


Running the examples
--------------------

The source code archives include examples. Archives are
`available on Github <https://github.com/pyglet/pyglet/releases/>`_:

.. code-block:: sh

    unzip pyglet-x.x.x.zip
    cd pyglet-x.x.x
    python examples/hello_world.py


As mentioned above, you can also clone the repository using Git:

.. code-block:: sh

    git clone https://github.com/pyglet/pyglet.git
    cd pyglet
    git checkout pyglet-1.5-maintenance
    python examples/hello_world.py
