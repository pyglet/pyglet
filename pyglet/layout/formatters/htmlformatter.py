#!/usr/bin/env python

'''Formatter for HTML markup.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from HTMLParser import HTMLParser
from htmlentitydefs import entitydefs

from pyglet.layout.css import Stylesheet
from pyglet.layout.formatters.documentformatter import *

# Default stylesheet for HTML 4 
# http://www.w3.org/TR/CSS21/sample.html
html4_default_stylesheet = Stylesheet('''
html, address,
blockquote,
body, dd, div,
dl, dt, fieldset, form,
frame, frameset,
h1, h2, h3, h4,
h5, h6, noframes,
ol, p, ul, center,
dir, hr, menu, pre   { display: block }
html            { font-family: serif }
li              { display: list-item }
head            { display: none }
table           { display: table }
tr              { display: table-row }
thead           { display: table-header-group }
tbody           { display: table-row-group }
tfoot           { display: table-footer-group }
col             { display: table-column }
colgroup        { display: table-column-group }
td, th          { display: table-cell }
caption         { display: table-caption }
th              { font-weight: bolder; text-align: center }
caption         { text-align: center }
body            { margin: 8px }
h1              { font-size: 2em; margin: .67em 0 }
h2              { font-size: 1.5em; margin: .75em 0 }
h3              { font-size: 1.17em; margin: .83em 0 }
h4, p,
blockquote, ul,
fieldset, form,
ol, dl, dir,
menu            { margin: 1.12em 0 }
h5              { font-size: .83em; margin: 1.5em 0 }
h6              { font-size: .75em; margin: 1.67em 0 }
h1, h2, h3, h4,
h5, h6, b,
strong          { font-weight: bolder }
blockquote      { margin-left: 40px; margin-right: 40px }
i, cite, em,
var, address    { font-style: italic }
pre, tt, code,
kbd, samp       { font-family: monospace }
pre             { white-space: pre }
button, textarea,
input, select   { display: inline-block }
big             { font-size: 1.17em }
small, sub, sup { font-size: .83em }
sub             { vertical-align: sub }
sup             { vertical-align: super }
table           { border-spacing: 2px; }
thead, tbody,
tfoot           { vertical-align: middle }
td, th          { vertical-align: inherit }
s, strike, del  { text-decoration: line-through }
hr              { border: 1px inset }
ol, ul, dir,
menu, dd        { margin-left: 40px }
ol              { list-style-type: decimal }
ol ul, ul ol,
ul ul, ol ol    { margin-top: 0; margin-bottom: 0 }
u, ins          { text-decoration: underline }
br:before       { content: "\A" }
/* XXX pseudo elements not supported yet
   :before, :after { white-space: pre-line } */
center          { text-align: center }
/* XXX pseudo elements not supported yet
    :link, :visited { text-decoration: underline }
    :focus          { outline: thin dotted invert } */

/* Begin bidirectionality settings (do not change) */
BDO[dir="ltr"]  { direction: ltr; unicode-bidi: bidi-override }
BDO[dir="rtl"]  { direction: rtl; unicode-bidi: bidi-override }

*[dir="ltr"]    { direction: ltr; unicode-bidi: embed }
*[dir="rtl"]    { direction: rtl; unicode-bidi: embed }
''')

class HTMLElement(DocumentElement):
    '''Element type for HTML.
    '''
    def __init__(self, name, attrs, parent, previous_sibling):
        super(HTMLElement, self).__init__(name, attrs, parent, previous_sibling)
        if attrs.has_key('id'):
            self.id = attrs['id']
        if attrs.has_key('class'):
            self.classes = attrs['class'].split()
        if attrs.has_key('style'):
            self.style = attrs['style']

class HTMLFormatter(HTMLParser, DocumentFormatter):
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

    # List of tags that are assumed to have no child data or elements.
    _auto_close_tags = ['br', 'hr', 'img']

    def __init__(self, render_device, locator):
        HTMLParser.__init__(self)
        DocumentFormatter.__init__(self, render_device)
        self.locator = locator
        self.add_stylesheet(html4_default_stylesheet)

    def format(self, data):
        if hasattr(data, 'read'):
            data = data.read()

        # Set up tree building
        self.box_stack = []
        self.tag_stack = []     # Elements can have different names to tags
        self.element_stack = []
        self.element_sibling_stack = [None]
        self.root_box = None
        self.content_buffer = ''
        self._in_p = False
        self._in_head = False

        # Invoke HTML parser
        self.feed(data)
        self.close()

        self.process_content_buffer()
        return self.root_box

    def handle_starttag(self, tag, attrs):
        name = tag
        attr_dict = {}
        for key, value in attrs:
            if key in ('class', 'id'):
                value = value.lower()
            attr_dict[key] = value

        if tag == 'head':
            self._in_head = True
        elif self._in_head and tag == 'style':
            self.content_buffer = ''

        if self._in_head:
            if name == 'link' and attr_dict.get('rel') == 'stylesheet':
                uri = attr_dict.get('href')
                if uri:
                    stream = self.locator.get_stream(uri)
                    if stream:
                        self.add_stylesheet(Stylesheet(stream))
    
            return

        self.process_content_buffer()

        # Fake the HTML formatting names (poorly).
        if name == 'font':
            name = 'span'
            style = ''
            if 'face' in attr_dict:
                style += 'font-family:%r;' % attr_dict['face']
            if 'size' in attr_dict:
                style += 'font-size:%s;' % \
                    self.font_sizes.get(attr_dict['size'],'medium')
            if 'color' in attr_dict:
                style += 'color:%s;' % attr_dict['color']
            attr_dict['style'] = style
        elif name == 'tt':
            name = 'span'
            attr_dict['style'] = 'font-family:monospace;'
        elif name == 'big':
            name = 'span'
            attr_dict['style'] = 'font-size:larger;'
        elif name == 'small':
            name = 'span'
            attr_dict['style'] = 'font-size:smaller;'
        elif name == 'hr':
            name = 'div'
            attr_dict['style'] = 'border-bottom:1px solid silver;' + \
                                 'border-top:1px solid gray;' + \
                                 'margin:.5em 0;'

        # Close prior unfinished tags if necessary.
        if self._in_p and tag == 'p':
            self.handle_endtag('p')

        # Create the element and box 
        if not self.root_box:
            elem = HTMLElement(name, attr_dict, None, None)
            box = self.create_box(elem)
            self.root_box = box
        else:
            elem = HTMLElement(name, attr_dict,
                self.element_stack[-1], self.element_sibling_stack.pop())
            self.element_sibling_stack.append(elem)
            box = self.create_box(elem)
            box.parent = self.box_stack[-1]

        self.apply_style(box)
        self.resolve_style_defaults(box)
        self.resolve_computed_values(box)

        if box.parent:
            self.add_child(box)
        if tag not in self._auto_close_tags:
            self.box_stack.append(box)
            self.tag_stack.append(tag)
            self.element_stack.append(elem)
            self.element_sibling_stack.append(None)

        if tag == 'p':
            self._in_p = True

    def handle_endtag(self, tag):
        if tag == 'style' and self._in_head:
            stylesheet = Stylesheet(self.content_buffer)
            self.add_stylesheet(stylesheet)
            self.content_buffer = ''
        elif tag == 'head':
            self._in_head = False
            self.content_buffer = ''

        if self._in_head:
            return

        self.process_content_buffer()

        if self.tag_stack[-1] == tag:
            # Correct nesting case
            self.box_stack.pop()
            self.tag_stack.pop()
            self.element_stack.pop()
            self.element_sibling_stack.pop()
        elif tag in self.tag_stack:
            # It's in the stack somewhere, keep popping until we get to it.
            while True:
                self.box_stack.pop()
                self.element_stack.pop()
                self.element_sibling_stack.pop()
                if self.tag_stack.pop() == tag:
                    break
        else:
            # It's not in the stack, just ignore it.
            pass

        if tag == 'p':
            self._in_p = False

    # Collect all data and process it at once
    def process_content_buffer(self):
        content = self.content_buffer
        self.content_buffer = ''

        if not self.box_stack:
            return
        self.add_text(content, self.box_stack[-1])

    def handle_data(self, data):
        self.content_buffer += data

    def handle_charref(self, name):
        print name
        raise NotImplementedError()

    def handle_entityref(self, name):
        self.content_buffer += entitydefs.get(name, '')
