#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

def create_render_device():
    from pyglet.text.layout import GLRenderDevice
    render_device = GLRenderDevice()
    render_device.width = 640
    render_device.height = 480
    return render_device

def render(data, formatter):
    from pyglet.layout.visual import VisualLayout
    box = formatter.format(data)
    layout = VisualLayout(formatter.render_device)
    layout.set_root(box)
    return layout

def render_xml(stylesheet, data, locator=None):
    from pyglet.layout.css import Stylesheet
    from pyglet.layout.formatters.xmlformatter import XMLFormatter

    if not locator:
        locator = LocalFileLocator()

    render_device = create_render_device()
    formatter = XMLFormatter(render_device, locator)
    formatter.add_stylesheet(stylesheet)
    return render(data, formatter)

def render_xhtml(data, locator=None):
    from pyglet.layout.locator import LocalFileLocator
    from pyglet.layout.formatters.xhtmlformatter import XHTMLFormatter
    from pyglet.image.layout import ImageBoxGenerator

    if not locator:
        locator = LocalFileLocator()
    render_device = create_render_device()

    formatter = XHTMLFormatter(render_device, locator)
    image_box_generator = ImageBoxGenerator(locator)
    formatter.add_generator(image_box_generator)
    return render(data, formatter)

def render_html(data, locator):
    from pyglet.layout.locator import LocalFileLocator
    from pyglet.layout.formatters.htmlformatter import HTMLFormatter
    from pyglet.image.layout import ImageBoxGenerator

    if not locator:
        locator = LocalFileLocator()
    render_device = create_render_device()

    formatter = HTMLFormatter(render_device, locator)
    image_box_generator = ImageBoxGenerator(locator)
    formatter.add_generator(image_box_generator)
    return render(data, formatter)

