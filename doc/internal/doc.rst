Documentation
=============

This is the pyglet documentation, generated with `Sphinx`_.

.. _Sphinx: https://sphinx-doc.org

.. _reStructuredText: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html

.. _autodoc: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

Details:

.. include:: build.rst

.. note::

   See the `Sphinx warnings log file <../warnings.txt>`_ for errors.


Writing documentation
---------------------

pyglet documentation is written in `reStructuredText`_, and built with `Sphinx`_.

layout
^^^^^^

The main documenation index is ``pyglet/doc/index.rst``. This file create three toctrees:

* The programming guide
* The API docs
* The development guide, which you are reading now


programming guide
-----------------



API documentation
-----------------

The API documentation is generated from the source code docstrings via `autodoc`_.


:Example:

   .. code-block:: python

    class Class1():
        """Short description of the class

        This is a good place for a general high level description
        of what the class is, and what it is used for.
        """

        def __init__(self, name: str, size: float):
            """Constructor description

            Here is where you can describe how to make an instance of the
            class. If any of the arguments need further explaination, that
            detail can be added as necessary.

            Args:
                name: The first argument description.
                size: The second argument description.
            """
            self.name = name
            self.size = size

            self.some_attribute: int = None

        def class_method(self, value: int) -> None:
            """Simple method description"""
            self.some_attribute = value

        def class_method_two(self, value: int) -> int:
            """Detailed method description

            You can add more details here.

            Args:
                value: The argument description.

            Returns:
                Describe what is being returned, if not already clear.
            """
            return self.some_attribute * 2


    def function_with_pep484_type_annotations(param1: int, param2: str) -> bool:
        """Example function with PEP 484 type annotations.

        Args:
            param1: The first parameter.
            param2: The second parameter.

        Returns:
           The return value. True for success, False otherwise.
        """
        ...


Building
--------

The complete documentation can be generated using ``sphinx``.
Make sure you prepare your environment as stated in :doc:`virtualenv`.

To build the documentation, execute::

   ./make.py docs --open


If the build succeeds, the web pages are in ``doc/_build/html``.

Optionally the standalone way to build docs is through
``setup.py`` or ``make``.

.. code:: bash

    # using setup.py (output dir: _build in project root)
    python setup.py build_sphinx

    # make (make.bat for windows)
    cd doc
    make html
