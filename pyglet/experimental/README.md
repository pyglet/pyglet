Experimental modules
====================

This package contains experimental modules, which are included here for
wider testing and feedback. Anything contained within may be broken, refactored,
or removed without notice.

A module may belong in `experimental` when it meets one or more of the following criteria:

- The API is still being designed.
- The implementation needs wider testing.
- The feature depends on external tools, generated assets, or optional workflows.
- The feature is useful, but too specialized for the core package.
- The feature introduces complexity that should not be required for normal users.
- The feature may eventually move into the stable package after review.

## Requirements 

Each experimental module should include documentation explaining:

- What the module solves or does.
- What tools, files, or assets are required.
- A minimal example, either as a `"__main__"` execution, or docstring.

## Graduation to stable API

An experimental module may be considered for promotion to the stable package when:

- The API has proven useful and reasonably stable.
- The feature has documentation and examples.
- Maintainers are willing to support it long-term.
