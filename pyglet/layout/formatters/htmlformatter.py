#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from HTMLParser import HTMLParser
from htmlentitydefs import entitydefs

from pyglet.layout.formatters.xhtmlformatter import XHTMLFormatter

class HTMLFormatter(HTMLParser, XHTMLFormatter):
    # HTML -> CSS font size mapping, based on 15.7 <absolute-size> table.
    font_sizes = {
        '1': 'xx-small',
        '2': 'small',
        '3': 'medium',
        '4': 'large',
        '5': 'x-large',
        '6': 'xx-large',
        '7': 'xx-large'
    }

    _auto_close_tags = ['br', 'hr', 'img']

    def __init__(self, render_device):
        HTMLParser.__init__(self)
        XHTMLFormatter.__init__(self, render_device)
        self._in_p = False

    def format(self, data):
        if hasattr(data, 'read'):
            data = data.read()
        self.startDocument()
        self.feed(data)
        self.close()
        self.endDocument()
        return self.root_box

    def handle_starttag(self, tag, attrs):
        attr_dict = {}
        for key, value in attrs:
            if key in ('class', 'id'):
                value = value.lower()
            attr_dict[key] = value

        # Fake the HTML formatting tags (poorly).
        if tag == 'font':
            tag = 'span'
            style = ''
            if 'face' in attr_dict:
                style += 'font-family:%r;' % attr_dict['face']
            if 'size' in attr_dict:
                style += 'font-size:%s;' % \
                    self.font_sizes.get(attr_dict['size'],'medium')
            if 'color' in attr_dict:
                style += 'color:%s;' % attr_dict['color']
            attr_dict['style'] = style
        elif tag == 'tt':
            tag = 'span'
            attr_dict['style'] = 'font-family:monospace;'
        elif tag == 'big':
            tag = 'span'
            attr_dict['style'] = 'font-size:larger;'
        elif tag == 'small':
            tag = 'span'
            attr_dict['style'] = 'font-size:smaller;'
        elif tag == 'hr':
            tag = 'div'
            attr_dict['style'] = 'border-bottom:1px solid silver;' + \
                                 'border-top:1px solid gray;' + \
                                 'margin:1em 0;'

        # Close unfinished tags if necessary.
        if self._in_p and tag == 'p':
            self.endElement('p')

        self.startElement(tag, attr_dict)

        if tag in self._auto_close_tags:
            self.endElement(tag)
        if tag == 'p':
            self._in_p = True

    def handle_endtag(self, tag):
        self.endElement(tag)
        if tag == 'p':
            self._in_p = False

    def handle_data(self, data):
        self.characters(data)

    def handle_charref(self, name):
        print name
        raise NotImplementedError()

    def handle_entityref(self, name):
        self.characters(entitydefs.get(name, ''))
