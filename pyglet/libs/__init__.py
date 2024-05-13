"""Platform-specific support components.

These consist of:

1. ctypes bindings for datastructures and functions
2. pyglet-specific wrapper functions around raw ctypes calls
3. vendored libraries in original or modified forms

When documenting these modules:

1. Use minimal formatting in any docstrings
2. Leave licenses at the tops of files in place

Simple docstrings with minimal formatting are best because:

1. No web doc is built for pyglet.lib
2. The docstrings will be used to debug complex platform issues
3. IDEs mangle formatting in any hover tooltips while debugging
"""
