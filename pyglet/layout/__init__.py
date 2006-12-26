#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

def render_xml_file(file):
    if type(file) in (str, unicode):
        file = open(file, 'r')
    return render_xml(file.read())

def render_xml(stylesheet, data):
    from xml.sax import parseString
    from pyglet.layout.css import Stylesheet
    from pyglet.layout.visual import VisualLayout
    from pyglet.layout.formatters.xml import XMLFormatter
    from pyglet.text.layout import GLRenderDevice

    render_device = GLRenderDevice()
    render_device.width = 640
    render_device.height = 480
    formatter = XMLFormatter(render_device)
    formatter.add_stylesheet(stylesheet)
    parseString(data, formatter)

    layout = VisualLayout(render_device)
    layout.set_root(formatter.root_box)
    return layout

def render_xhtml(data):
    from xml.sax import parseString
    from pyglet.layout.visual import VisualLayout
    from pyglet.layout.formatters.xhtml import XHTMLFormatter
    from pyglet.text.layout import GLRenderDevice

    render_device = GLRenderDevice()
    render_device.width = 640
    render_device.height = 480
    formatter = XHTMLFormatter(render_device)
    parseString(data, formatter)

    layout = VisualLayout(render_device)
    layout.set_root(formatter.root_box)
    return layout


