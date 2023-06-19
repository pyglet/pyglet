Development environment
=======================

To develop pyglet, you need an environment with at least the following:

    - |min_python_version_fancy_str|
    - `pytest <https://pytest.org>`_
    - Your favorite Python editor or IDE

All requirements should already be located in ``doc/requirements.txt``
and ``tests/requirements.txt``.

.. code::

    pip install -r doc/requirements.txt
    pip install -r tests/requirements.txt

To use and test all pyglet functionality you should also have:

    - `FFmpeg <https://www.ffmpeg.org/download.html>`_
    - `Pillow <https://pillow.readthedocs.io>`_
    - `coverage <https://coverage.readthedocs.io>`_

To build packages for distribution you need to install:

    - `wheel <https://github.com/pypa/wheel/>`_

It is preferred to create a Python virtual environment to develop in.
This allows you to easily test on all Python versions supported by pyglet,
not pollute your local system with pyglet development dependencies,
and not have your local system interfere with pyglet developement.
All dependencies you install while inside an activated virtual
environment will remain isolated inside that environment.
When you're finished, you can simply delete it.

This section will show you how to set up and use virtual environments.
If you're already familiar with this, you can probably skip the rest of
this page.

Linux or Mac OSX
----------------

Setting up
''''''''''

Setting up a virtual environment is almost the same for Linux and OS X.
First, use your OS's package manager (apt, brew, etc) to install the
following dependencies:

    - |min_python_version_fancy_str|

To create virtual environments, ``venv`` is included in the standard
library since Python 3.3.

Depending on your platform, python may be installed as ``python`` or ``python3``.
You may want to check which command runs python 3 on your system::

    python --version
    python3 --version

For the rest of the guide, use whichever gives you the correct python version on your system.
Some linux distros may install python with version numbers such as
|min_python_version_package_name|, so you may need to set up an alias.

Next, we'll create a virtual environment.
Choose the appropriate command for your system to create a virtual environment::

    python -m venv pyglet-venv
    python3 -m venv pyglet-venv

Once the virtual environment has been created, the next step is to activate
it. You'll then install the dependencies, which will be isolated
inside that virtual environment.

Activate the virtual environment ::

   . pyglet-venv/bin/activate

You will see the name of the virtual environment at the start of the
command prompt.

[Optional] Make sure pip is the latest version::

    pip install --upgrade pip

Now install dependencies in ``doc/requirements.txt`` and
``tests/requirements.txt``::

    pip install -r doc/requirements.txt
    pip install -r tests/requirements.txt

Finishing
'''''''''

To get out of the virtual environment run::

   deactivate

Windows
-------

Setting up
''''''''''

Make sure you download and install:

    - |min_python_version_fancy_str| from the
      `official Python site <http://www.python.org/downloads/windows/>`_

Pip should be installed by default with the latest Python installers.
Make sure that the boxes for installing PIP and adding python to PATH are checked.

When finished installing, open a command prompt.

To create virtual environments, ``venv`` is included in the standard library
since Python 3.3.

Next, we'll create a virtual environment.::

    python -m venv pyglet-venv

Once the virtual environment has been created, the next step is to activate
it. You'll then install the dependencies, which will be isolated
inside that virtual environment.

Activate the virtual environment ::

   . pyglet-venv/bin/activate

You will see the name of the virtual environment at the start of the
command prompt.

[Optional] Make sure pip is the latest version::

   pip install --upgrade pip


Now install dependencies in ``doc/requirements.txt`` and
``tests/requirements.txt``::

    pip install -r doc/requirements.txt
    pip install -r tests/requirements.txt

Finishing
'''''''''

To get out of the virtual environment run::

   deactivate
