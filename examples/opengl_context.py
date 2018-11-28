#!/usr/bin/python
# $Id:$

"""In order to use the features of modern OpenGL versions, you must ask for
a specific context version. You can do this by supplying the `major_version`
and `minor_version` attributes for a GL Config.

This example creates an OpenGL 3 context, prints the version string to stdout,
and exits.
"""

from __future__ import print_function

import pyglet

# Specify the OpenGL version explicitly to request 3.0 features, including
# GLSL 1.3.
#
# Some other attributes relevant to OpenGL 3:
#   forward_compatible = True       To request a context without deprecated
#                                   functionality
#   debug = True                    To request a debug context
config = pyglet.gl.Config(major_version=3, minor_version=0)

# Create a context matching the above configuration.  Will fail if
# OpenGL 3 is not supported by the driver.
window = pyglet.window.Window(config=config, visible=False)

# Print the version of the context created.
print('OpenGL version:', window.context.get_info().get_version())

window.close()
