Installation
============

.. note:: These instructions apply to pyglet |version|.

pyglet is a pure Python library, with no hard dependencies on other modules.
No special steps or complitation are required for installation. You can install
from `on PyPI <https://pypi.python.org/pypi/pyglet>`_ via **pip**. For example:

.. code-block:: sh

    pip install --upgrade --user pyglet

You can also clone the repository using **git** and install from source:

.. code-block:: sh

    git clone https://github.com/pyglet/pyglet.git
    cd pyglet
    python setup.py install --user


In addition, since pyglet is pure Python, you can also just copy the `pyglet`
subfolder directly into the root of your project without installation into your
local `site-packages`.

To play video, or a wide selection of compressed audio, pyglet can optionally
use `FFmpeg <https://www.ffmpeg.org/download.html>`_.


Running the examples
--------------------

The source code archives include examples. Archive zip files are
`available on Github <https://github.com/pyglet/pyglet/releases/>`_:

.. code-block:: sh

    unzip pyglet-x.x.x.zip
    cd pyglet-x.x.x
    python examples/hello_world.py


As mentioned above, you can also clone the repository using Git:

.. code-block:: sh

    git clone https://github.com/pyglet/pyglet.git
    cd pyglet
    python examples/hello_world.py
