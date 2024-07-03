============================
Documentation and Type Hints
============================

The pyglet documentation is written in `reStructuredText`_ (RST), and built with `Sphinx`_.
If you are not familiar with reStructuredText, it is similar to MarkDown but offers more
robust functionality for creating technical documentation. This is the default language
used in Sphinx. Most of the documentation is written in plain ascii text, so you can still
modify or add to it without needing to know much RST syntax.

The documentation can be found as part of the pyglet repository, under the ``doc``
subfolder. The main index is located at ``pyglet/doc/index.rst``, which includes the
main landing page, and defines three toctrees:

* The programming guide
* The API docs
* The development guide


programming guide
-----------------
The programming guide is made up of many individual `.rst` files, which are located
in the repository under the ``pyglet/doc/programming_guide/`` folder. All files in this
folder are also defined in the index.rst, in order to includes them in the build process.


API documentation
-----------------
The API documentation is generated direclty from the source code docstrings by `autodoc`_,
a plugin extension that is included with Sphinx. The generation itself is mostly automatic,
but declaration files are necessary to instruct Sphinx how and which modules and classes
should be included. Look through the existing files at ``pyglet/doc/modules/`` to get an
idea of what this looks like.

docstring rules
^^^^^^^^^^^^^^^
- Google Format with no typing.
- Docstrings are meant primarily for user or general information, not implementation details.
- Hash (``#``) comments should be used for developers or contributors when needing to provide information to other developers.
- Any methods or functions without a docstring will not appear in the API documentation.
- Documentation will hide private attributes unless otherwise overridden in the rst.
- Parameter descriptions are not required if straight forward enough, unless a clarification is needed.
- If you have to add a parameter description, you must add one for each in that function. (None or All)
- A return description is optional.
- All classes and functions should have a header with at least a one line succinct description.
- For class attributes, use ``Attributes:`` in the header. Type hints may be specified, as currently they are not picked up automatically.
    - Required: You will also need to add these ``:exclude-members: <attribute>`` in the rst files manually. Otherwise, autodoc will pick it up twice.
    - Class attributes are generally meant to be used for:
        a. Changing global behavior to the class in some form. (Example: ``Texture.default_mag_filter``)
        b. Simplifying subclassing for users. (Example: group_class for Sprite)
        c. Troubleshooting purposes.

- Parameter descriptions should be indented on a new line for clarity.
- Parameter descriptions can have one line of space between each for clarity.
- For class instance attributes, these should be documented with a #: <description> comment.
- For class instance attributes you wish to hide from the docs. Either:
    a. Consider making them private (via ``_name``) if it makes sense.
    b. Mark them with a comment in this format: #: :meta private:

typing rules
^^^^^^^^^^^^
- Do not put type information in docstrings, rely on annotations.
- If you are using class annotations, you must have ``from __future__ import annotations`` at the top of the module.
- When adding annotations, if a class type is not used in the file, it must be imported only within TYPE_CHECKING
- No need to go overboard, some rules can be set to ignored if there is not yet an adequate way to do it.
- Return types always need to be specified even if ``None``.

example
^^^^^^^

.. code-block:: python

    class Class1():
        """Short description of the class

        This is a good place for a general high level description
        of what the class is, and what it is used for. For example:
        Class1 is used for X and Y, which makes Z possible, etc.
        """

        #: This is the default thing.
        some_default_thing: float = 123.0

        #: :meta private:
        dont_show_me: int = 456

        def __init__(self, name: str, size: float):
            """Constructor description

            Here is where you can describe how to make an instance of the
            class. If any of the arguments need further explaination, that
            detail can be added as necessary. For example:
            You must provide a name and a size, etc. etc.

            Args:
                name: The name of this object.
                size: The size, in centimeters.
            """
            self.name = name
            self.size = size

            #: :This will show in the docs
            self.attribute_one: int = None

            self.attribute_two: str = "hello"

        def set_size(self, centimeters: float) -> None:
            """Simple description + type hints are enough."""
            self.size = centimeters

        def calculate_scaled_size(self, scale: float) -> float:
            """Detailed method description

            You can add more details here.

            Args:
                scale: The argument description.

            Returns:
                Describe what is being returned, if not already clear.
            """
            # This is a developer comment, which is not intended for end users to
            # see. These can be used to explain to future developers why something
            # is implemented a certain way, or any other developer focused notes, etc.
            return self.size * scale


    def function_with_pep484_type_annotations(param1: int, param2: str) -> bool:
        """Example function with PEP 484 type annotations.

        Args:
            param1: The first parameter.
            param2: The second parameter.

        Returns:
           When necessary, you can describe the return value in
           more detail. This can be skipped if it's obvious from
           the return type hint.
        """
        ...

documentation tips
^^^^^^^^^^^^^^^^^^

Sometimes you may, or may not want certain class attributes to show up in the API
docs. Depending on how and where you put the annotations and/or comments, you can
control what gets picked up during the documentation building. Some examples are
shown below.

The following will show in docs WITHOUT docstring::

    class Test:
        blah: int

The following will show in docs WITH docstring::

    class Test:
        #: :My description.
        blah: int

The following will NOT show in the docs::

    class Test:
        def __init__(self):
            self.blah: int = 0


The following will show in the docs::

    class Test:
        def __init__(self):
            #: :This is documented.
            self.blah: int = 0


Developer reference
-------------------
Developer focused documentation is located in the ``pyglet/doc/internal/`` folder.
This contains various pages about tools that are used with developing pyglet, the
documentation page that you're reading now, information on unit tests, etc. These
pages are useful for anyone who wants to contribute.

building
^^^^^^^^
Building the documentation locally requires a few dependencies. See :doc:`virtualenv`
for more information on how to install them. Once you have Sphinx and it's dependencies
installed, you can proceed with the build. The first way to build is by using pyglet's
included `make.py` utility. This is found in the root of the repository, and includes
some helper functions for common build and distribution related tasks. For docs, execute::

   ./make.py docs --open


If the build succeeds, a browser window will open. You can skip this by omitting `--open`.
The generated static web pages will be in ``doc/_build/html``.

You can also build the documentation by using Sphinx's ``Makefile``:

.. code:: bash

    cd pyglet/doc
    make html       # Posix
    make.bat html   # Windows


Note that there are also additional build targets beyond HTML, but
they may require installing additional dependencies. Run ``make help``
to see a list of them:

.. code:: console

   $ make help
   Please use `make <target>' where <target> is one of
   html       to make standalone HTML files
   dirhtml    to make HTML files named index.html in directories
   singlehtml to make a single large HTML file
   pickle     to make pickle files
   json       to make JSON files
   htmlhelp   to make HTML files and a HTML help project
   qthelp     to make HTML files and a qthelp project
   devhelp    to make HTML files and a Devhelp project
   epub       to make an epub
   latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter
   latexpdf   to make LaTeX files and run them through pdflatex
   text       to make text files
   man        to make manual pages
   texinfo    to make Texinfo files
   info       to make Texinfo files and run them through makeinfo
   gettext    to make PO message catalogs
   changes    to make an overview of all changed/added/deprecated items
   linkcheck  to check all external links for integrity
   doctest    to run all doctests embedded in the documentation (if enabled)


auto-generated details
^^^^^^^^^^^^^^^^^^^^^^

.. include:: build.rst


.. _Sphinx: https://sphinx-doc.org

.. _reStructuredText: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html

.. _autodoc: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
