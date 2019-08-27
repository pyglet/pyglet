# Contributing to Lektor-Icon


First off, thanks for your interest in helping out!

**Important Note:** Keep in mind that the original and a continuing purpose of the code in this repository is to provide a high-quality, modern theme for the [Spyder](https://www.spyder-ide.org/) website.
Therefore, all additions, changes and removals should should strive to retain compatibility, to the extent practicable, with its usage there.
If not possible, please discuss them with us first.
Thanks!

For more guidance on the basics of using ``git`` and Github to contribute to Lektor-Icon and other projects, check out the tutorial in the [Spyder Development Documentation](https://github.com/spyder-ide/spyder/wiki/Contributing-to-Spyder) for detailed instructions, and be sure to see the [Spyder Contributing Guide](https://github.com/spyder-ide/spyder/blob/master/CONTRIBUTING.md) for [guidelines on adding third party content to Lektor-Icon](https://github.com/spyder-ide/spyder/blob/master/CONTRIBUTING.md#adding-third-party-content) (like images, fonts, CSS stylesheets and Javascript libraries, as well as Jinja2 templates from other projects).
As always, feel free to contact us via one of the platforms listed at the bottom of this document if you have any questions or concerns, and we look forward to reviewing your contribution to Lektor-Icon!



## Reporting Issues

If you encounter an issue using Lektor-Icon, spot a bug in the code, or have a suggestion for improving it further, please let us know by submitting a report on our [Github Issue Tracker](https://github.com/spyder-ide/lektor-icon/issues).
Make sure you provide as much information as possible to help us track down the issue, and we always appreciate offers to help resolve it yourself.
Thanks!



## Submitting Pull Requests

We welcome contributions from the community, and will do our best to review all of them in a timely fashion.
To do so, please fork this repository, create a new feature branch there based off the latest ``master``, make and test your changes, and then submit a pull request (PR) to this repo.
Please make sure your PR titles are brief but descriptive, and include ``PR: `` as a prefix (if a work in progress, also prefix ``[WiP]``).

You should also create a corresponding issue as well if your change is substantive, so that we can keep track of everything and give you credit for closing it.
You might want to open an issue first discussing your changes, to get feedback and suggestions before implementing them.



## Standards and Conventions

Make sure you follow these to ensure clarity, consistency and correctness throughout our codebase.

### All Files

* **UTF-8** for character encoding
* **LF** for newlines (our ``.gitattributes`` enforces this on commit)
* **ISO 8601** (YYYY-MM-DD HH:MM:SS) for dates/times
* **SI/metric** for units
* **HTTPS** for all links where available (try adding it if the site is HTTP by default)
* **Decimal point**, rather than decimal comma
* **Forward slashes** (``/``) for path delimiters on all platforms (Windows accepts them equally to backslashes)
* **Strip trailing spaces** on save
* **Newline-terminate** all files
* **Spaces, not tabs** except where e.g. JS files are unmodified or nearly so
* **Lowercase filenames and extensions**, not all upper
* **Dash-deliminate filenames** (``test-file.txt``), not underscore (``test_file.txt``)
* **.txt** extension for all plain text files


### All Lektor files (INI and ``contents.lr``)

* **No hard wrap** after a fixed character value
* **No indents/leading spaces** should be used
* **Use ``true``/``false``, not ``yes``/``no``** for boolean values
* **Include all keys**, even if values left blank
* **Adhere to the Lektor theme spec** as published in the docs


### Lektor ``contents.lr``

* **Use a hierarchy of line breaks** between flowblock levels; respect existing convention
* **Line breaks after ``---``** where needed, never before
* **One blank line before multiline content**, i.e. blocks that span multiple lines
* **Line break after sentences** (like this document)


### INI Files (Models, Flowblocks, Lektorproject, etc)

* **No quoting of values** should be employed
* **One space around equals** on both sides
* **One blank line between groups** of property values
* **All lowercase names** for groups and keys unless required


### Models and Flowblocks

* **Name each model** clearly and appropriately
* **Always include a label** for each item
* **Include a short description** of each item for the admin UI; at least one sentence, but may extend to multiple if needed.
* **Make titles size = large** unless in a multi-level nested flowblock
* **Always include a checkbox label** for checkboxes
* **Adhere to group and property order** as listed in the Lektor documentation


### Jinja2 HTML Templates

* **Ensure correct indent levels in output**; i.e. don't add indent levels solely for Jinja statements
* **Indent jinja statements equally** to surrounding HTML
* **One space after ``(%``, ``{{``, and ``|``/before ``%}``, ``}}`` and ``|``**
* **Use ``'`` in Jinja, ``"`` in HTML** for quotes
* **Follow spirit of PEP 8** for code style in Jinja expressions
* **Use ``asseturl`` for anything in the ``assets/`` directory


### HTML

* **Validate with W3C HTML5 checker** against latest HTML standards
* **Two space indent** for all files
* **Don't use deprecated elements** in HTML5
* **Avoid inline styles** if at all possible
* **Don't close single tags** e.g. XHTML-style ``<br/>``
* **Explicitly declare MIME types** to avoid content-sniffing
* **Explicitly specify UTF-8 encoding** on elements where possible


### CSS

* **Validate with W3C CSS3 checker** against latest CSS standards
* **No vendor prefixes** unless absolutely necessary; ensure parity between vendors
* **Two space indent** for all CSS stylesheets
* **One blank line between blocks** unless very closely linked
* **One selector per line** unless extremely short
* **Always terminate properties with ``;``** even if the last in the block
* **Use six-digit hex for colors** unless transparency needed
* **One space after ``:`` and before ``{``** except in pseudo-classes
* **K&R style brackets** for each block
* **Prefer ``em``/``rem`` to ``px``** where practicable


### Javascript

* **Follow existing code style** when it doubt
* **Conform to modern ES6 best practices** where possible
* **Four space indent** for new files
* **Spaces after commas** except between linebreaks
* **Spaces around binary operators** like PEP8
* **K&R style brackets** for each block
* **Use ``'`` for quotes**, except for HTML snippits
* **Include descriptive comments**, at least one per function
* **Maintain existing blank line hierarchy** between blocks
* **Use minified version** of external libraries


### Python

* **Python 2/3 "universal" code** until the Python 2 EOL date
* **PEP 8** style for Python code, with all recommendations treated as requirements unless noted
* **PEP 257** for all docstrings
* **79 characters** for line length
* **Check code with ``pylint``** (or another linter) before submitting to catch potential errors and bad practices


### Images

* **SVG, PNG or JPEG for all images**; no exotic or proprietary formats
* **SVG > PNG** when available for graphics and other vectorizable images
* **PNG > JPEG, except for photos** whenever possible
* **Size images appropriately** for the intended use; make use of responsive images when available
* **Run ``optipng -o7``** on all PNGs; use moderate quality for JPEGs
* **Alt text** should be always be provided describing the content of each image


### Fonts

* **Include TTF, WOFF and WOFF2** format files for each font as available
* **Deploy only WOFF2 > WOFF** if present
* **Subset fonts** if only a few characters are used


### Documentation

* **Github-Flavored Markdown** (GFM) for documentation like this one
* **Universal Markdown/reStructured Text syntax** where practicable, e.g. double backtick instead of single for code, ``*`` for bullets instead of ``-``, and ``*``/``**`` for italic/bold instead of ``_``/``__``.
* **No hard wrap** after a certain character value
* **Line break after sentences** (like this document)
* **3/2/1 lines before L2/3/4+ headings**, except for the first heading



## Roadmap

Nothing concrete at the moment, but a few ideas:

* Refactor large ``style.css`` into separate stylesheets for blog/pages, mainpage and both
* Refactor Javascript to use native ES6 instead of jQuery
* Add polyfill/better fallback for theme coloring

* Include per-services, team etc card to make the whole card a clickable link
* Implement specific functionality around blog categories and tags
* Make generic pages more sophisticated, and/or introduce additional page types



Thanks so much!
