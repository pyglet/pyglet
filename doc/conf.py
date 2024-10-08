#
# pyglet documentation build configuration file.
#
# This file is execfile()d with the current directory set to its containing dir.
import os
import sys
import time
import typing
import datetime

from typing import TypeVar

import sphinx_autodoc_typehints

# -- Extensions to the  Napoleon GoogleDocstring class ---------------------
from sphinx.ext.napoleon.docstring import GoogleDocstring
from sphinx.parsers import RSTParser


def parse_attributes_section(self, section):
    # Combination of _format_fields and _parse_attributes_section to get type hints loaded properly using
    # the theme and getting the custom name instead of Specifying just 'Variables'
    field_type = "Class Variables"
    fields = self._consume_fields()

    field_type = ":%s:" % field_type.strip()
    padding = " " * len(field_type)
    multi = len(fields) > 1
    lines: list[str] = []
    for _name, _type, _desc in fields:
        if not _type:
            _type = self._lookup_annotation(_name)
            if _name in self._annotations:
                _type = sphinx_autodoc_typehints.add_type_css_class(
                    sphinx_autodoc_typehints.format_annotation(self._annotations[_name], self._app.config))

        field = self._format_field(_name, _type, _desc)
        if multi:
            if lines:
                lines.extend(self._format_block(padding + " * ", field))
            else:
                lines.extend(self._format_block(field_type + " * ", field))
        else:
            lines.extend(self._format_block(field_type + " ", field))
    if lines and lines[-1]:
        lines.append("")
    return lines


GoogleDocstring._parse_attributes_section = parse_attributes_section


# Unpatch... the patch.
def _revert_patch():
    pass


sphinx_autodoc_typehints.patches._patch_google_docstring_lookup_annotation = _revert_patch


# Patch to fix our RST insertion issues.
class _RstSnippetParser(RSTParser):
    @staticmethod
    def decorate(_content) -> None:
        """Override to skip processing rst_epilog/rst_prolog for typing."""


sphinx_autodoc_typehints.parser.RSTParser = _RstSnippetParser


def write_build(data, filename):
    with open(os.path.join("internal", filename), "w") as f:
        f.write(".. list-table::\n")
        f.write("   :widths: 50 50\n")
        f.write("\n")
        for var, val in data:
            f.write("   * - " + var + "\n     - " + val + "\n")


sys.is_pyglet_doc_run = True

document_modules = ["pyglet"]

# Patched extensions base path.
sys.path.insert(0, os.path.abspath("."))

# import the pyglet package.
sys.path.insert(0, os.path.abspath(".."))

try:
    import pyglet

    print(f"Generating pyglet {pyglet.version} Documentation")
except ImportError:
    print("ERROR: pyglet not found")
    sys.exit(1)

# -- PYGLET DOCUMENTATION CONFIGURATION ----------------------------------------


# Set up substitutions that can be referenced later.
# IMPORTANT:
# Substitutions are moody and NEED control-like characters to be escaped
# after them. For example, in |min_python_version|\+ , escaping the plus
# sign is crucial to avoiding incomprehensible errors.
# For convenience, |min_python_version_fancy_str| is defined below to
# avoid having to deal with syntax errors.
# Also, please note that there does not appear to be a good way to use
# substitutions within link text by default.
rst_epilog = rf"""
.. |min_python_version| replace:: {pyglet.MIN_PYTHON_VERSION_STR}
.. |min_python_version_package_name| replace:: ``python{pyglet.MIN_PYTHON_VERSION_STR}``
.. |min_python_version_fancy_str| replace:: Python {pyglet.MIN_PYTHON_VERSION_STR}\+
"""

implementations = ["cocoa", "win32", "xlib"]

# For each module, a list of submodules that should not be imported.
# If value is None, do not try to import any submodule.
skip_modules = {"pyglet": {
                     "pyglet.lib": None,
                     "pyglet.libs": None,
                     "pyglet.app": implementations,
                     "pyglet.display": implementations + ["xlib_vidmoderestore"],
                     "pyglet.extlibs": None,
                     "pyglet.font": ["quartz",
                                     "win32",
                                     "freetype",
                                     "freetype_lib",
                                     "fontconfig",
                                     "win32query"],
                     "pyglet.input": ["darwin_hid",
                                      "directinput",
                                      "evdev",
                                      "wintab",
                                      "x11_xinput", "x11_xinput_tablet"],
                     "pyglet.image.codecs": ["gdiplus",
                                             "gdkpixbuf2",
                                             "pil",
                                             "quartz",
                                             "quicktime"],
                     "pyglet.gl": implementations + ["agl",
                                                     "glext_arb", "glext_nv",
                                                     "glx", "glx_info",
                                                     "glxext_arb", "glxext_mesa", "glxext_nv",
                                                     "lib_agl", "lib_glx", "lib_wgl",
                                                     "wgl", "wgl_info", "wglext_arb", "wglext_nv"],
                     "pyglet.media.drivers": ["directsound",
                                              "openal",
                                              "pulse"],
                     "pyglet.window": implementations,
                        },
                }

now = datetime.datetime.fromtimestamp(time.time())
build_data = (("Date", now.strftime("%Y/%m/%d %H:%M:%S")),
              ("pyglet version", pyglet.version))
write_build(build_data, "build.rst")

# -- SPHINX STANDARD OPTIONS ---------------------------------------------------

autosummary_generate = False

# -- General configuration -----------------------------------------------------
#
# Note that not all possible configuration values are present in this file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

inheritance_graph_attrs = dict(rankdir="LR", size='""')

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ["sphinx.ext.autodoc",
              "sphinx.ext.napoleon",
              "sphinx.ext.intersphinx",
              "sphinx.ext.inheritance_diagram",
              "sphinx.ext.todo",
              "sphinx_autodoc_typehints",
              ]

# Autodoc settings.
autodoc_member_order = "groupwise"

# Separate init from the class header as RTD theme makes it all the same color, reducing readability.
autodoc_class_signature = "separated"

# Add type hints to description and parameters in docs.
autodoc_typehints = "signature"
autodoc_typehints_format = "short"

# Configuration for sphinx_autodoc_typehints
typehints_use_signature = True
typehints_use_signature_return = True
always_use_bars_union = True

# Enable links to Python's main doc
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "pyglet"
copyright = "2006-2008, Alex Holkner. 2008-2023 pyglet contributors"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = "2.0"
# The full version, including alpha/beta/rc tags.
release = pyglet.version

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
# language = 'en'

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
# today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "_templates", "api"]

# The reST default role (used for this markup: `text`) to use for all documents.
# default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
# add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = False

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# A list of ignored prefixes for module index sorting.
modindex_common_prefix = ["pyglet."]

# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
# html_theme_options = {}

# Force custom css to allow multiline inits.
html_css_files = [
    "css/custom.css",
]
html_style = "css/custom.css"

# Add any paths that contain custom themes here, relative to this directory.
# html_theme_path = ["ext/theme"]

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = f"pyglet v{pyglet.version}"

# A shorter title for the navigation bar.  Default is the same as html_title.
html_short_title = f"pyglet v{pyglet.version} documentation "

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "_static/logo.png"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_static/favicon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
# html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
# html_additional_pages = {}

# If false, no module index is generated.
html_domain_indices = True

# If false, no index is generated.
html_use_index = True

# If true, the index is split into individual pages for each letter.
html_split_index = True

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
# html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
# html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = "pygletdoc"

# -- Options for LaTeX output --------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    # 'preamble': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
    ("index", "pyglet.tex", "pyglet Documentation",
     "Alex Holkner", "manual"),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
# latex_use_parts = False

# If true, show page references after internal links.
# latex_show_pagerefs = False

# If true, show URL addresses after external links.
# latex_show_urls = False

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
# latex_domain_indices = True


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ("index", "pyglet", "pyglet Documentation",
     ["Alex Holkner"], 1),
]

# If true, show URL addresses after external links.
# man_show_urls = False


# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    ("index", "pyglet", "pyglet Documentation",
     "Alex Holkner", "pyglet", "One line description of project.",
     "Miscellaneous"),
]

# Documents to append as an appendix to all manuals.
# texinfo_appendices = []

# If false, no module index is generated.
# texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
# texinfo_show_urls = 'footnote'

python_maximum_signature_line_length = 85

nitpicky = True


def custom_formatter(annotation, config):
    # Fixes TypeVar bounds, where the bound reference is forward referenced and class cannot be determined.
    # Defaults to a class style. Seems good enough for now since most bound things are classes.
    if isinstance(annotation, TypeVar):
        try:
            module = sphinx_autodoc_typehints.get_annotation_module(annotation)
            class_name = sphinx_autodoc_typehints.get_annotation_class_name(annotation, module)
            args = sphinx_autodoc_typehints.get_annotation_args(annotation, module, class_name)
        except ValueError:
            return str(annotation).strip("'")
        params = {k: getattr(annotation, f"__{k}__") for k in ("bound", "covariant", "contravariant")}
        params = {k: v for k, v in params.items() if v}
        if "bound" in params:
            bound_param = params["bound"]
            if isinstance(bound_param, typing.ForwardRef):
                # May be wrong but
                params["bound"] = f":py:class:`{bound_param.__forward_arg__}`"
            else:
                params["bound"] = f"{sphinx_autodoc_typehints.format_annotation(bound_param, config)}"
        args_format = f"\\(``{annotation.__name__}``{', {}' if args else ''}"
        if params:
            args_format += "".join(f", *{k} =* {v}" for k, v in params.items())
        args_format += ")"
        formatted_args = None if args else args_format
        return f":py:class:`TypeVar` {formatted_args}"
    return None


typehints_formatter = custom_formatter
