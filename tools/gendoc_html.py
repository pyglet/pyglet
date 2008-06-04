#!/usr/bin/env python
# $Id:$

import optparse
import os
import os.path
import re
import shutil
import subprocess

from docutils.core import publish_doctree, publish_from_doctree
from docutils.utils import new_document
from docutils.writers import html4css1
from docutils import nodes

from epydoc.markup.doctest import HTMLDoctestColorizer

class HTMLWriter(html4css1.Writer):
    def __init__(self):
        html4css1.Writer.__init__(self)
        self.translator_class = HTMLTranslator

class HTMLTranslator(html4css1.HTMLTranslator):
    def visit_reference(self, node):
        # Copied from html4css1.Writer but extended to add "title" attribute.
        if node.has_key('refuri'):
            href = node['refuri']
            if ( self.settings.cloak_email_addresses
                 and href.startswith('mailto:')):
                href = self.cloak_mailto(href)
                self.in_mailto = 1
        else:
            assert node.has_key('refid'), \
                   'References must have "refuri" or "refid" attribute.'
            href = '#' + node['refid']
        atts = {'href': href, 'class': 'reference'}
        if not isinstance(node.parent, nodes.TextElement):
            assert len(node) == 1 and isinstance(node[0], nodes.image)
            atts['class'] += ' image-reference'
        if node.has_key('link_class'):
            atts['class'] += ' %s' % node['link_class']
        if node.has_key('title'):
            atts['title'] = node['title']
        self.body.append(self.starttag(node, 'a', '', **atts))

def convert_image(uri, input_dir, html_dir):
    '''Convert image found at uri in input_dir to something useable and place
    in html_dir.  Return the new uri.'''

    # Bail if it's external
    if uri.startswith('http:'):
        return uri

    input_file = os.path.join(input_dir, uri)
    if not os.path.exists(input_file):
        print 'Not found: %s' % uri
        return uri

    if uri.endswith('.svg'):
        # Convert SVG to PNG using Inkscape
        newuri = '%s.png' % os.path.splitext(os.path.basename(uri))[0]
        output_file = os.path.join(html_dir, newuri)
        #subprocess.call('convert %s %s' % (input_file, output_file),
        #                shell=True)
        subprocess.call('inkscape --export-png=%s %s' % \
                            (output_file, input_file),
                        shell=True)
        return newuri
    elif uri.endswith('.png') or uri.endswith('.jpg'):
        # Copy image to output dir
        output_file = os.path.join(html_dir, uri)
        shutil.copy(input_file, output_file)
        return uri
        

def shorten(title):
    words = title.split()
    if len(words) <= 3:
        return ' '.join(words)
    else:
        return ' '.join(words[:2]) + ' ...'

class Page(object):
    def __init__(self, document, filename, parent, ids):
        self.document = document
        self.filename = filename
        self.parent = parent
        self.ids = ids
        self.children = []

        # Look for breadcrumb name (title)
        self.title = None
        for field in [n for n in document.traverse() \
                        if isinstance(n, nodes.field)]:
            i = field.first_child_matching_class(nodes.field_name)
            if field[i].astext() == 'breadcrumb':
                j = field.first_child_matching_class(nodes.field_body)
                self.title = field[j].astext()
                field.parent.remove(field)

        # No breadcrumb field, use title
        if self.title is None:
            title_i = document.first_child_matching_class(nodes.Titular)
            if title_i is not None:
                self.title = self.document[title_i].astext()
            else:
                self.title = self.filename
        document['title'] = self.title
 
    def split(self, depth):
        # Remove sections that are children of document and create
        # new pages out of them.
        for section in [n for n in self.document.children \
                        if isinstance(n, nodes.section)]:
            self.document.children.remove(section)

            ids = section.attributes['ids']
            filename = '%s.html' % ids[0].replace('-', '_')
            document = new_document(filename)
            for child in section.children:
                document += child.deepcopy()
            page = Page(document, filename, self, ids)
            self.children.append(page)
            if depth:
                page.split(depth - 1)

    def collect_ids(self, id_map):
        for id in self.ids:
            id_map[id] = self.filename

        for node in self.document.traverse():
            if hasattr(node, 'attributes'):
                for id in node.attributes.get('ids', ()):
                    uri = '%s#%s' % (self.filename, id)
                    id_map[id] = uri

        for child in self.children:
            child.collect_ids(id_map)

    def add_refuri(self, id_map):
        for node in self.document.traverse():
            if hasattr(node, 'attributes'):
                refid = node.attributes.get('refid')
                if refid in id_map:
                    node.attributes['refuri'] = id_map[refid]

        for child in self.children:
            child.add_refuri(id_map)

    def add_navigation(self, previous, next):
        navigation = nodes.container()
        navigation['classes'] += ['navigation']
        paragraph = nodes.paragraph()
        navigation += paragraph

        if previous:
            inline = nodes.inline()
            inline['classes'] += ['previous']
            inline += nodes.Text('Previous: ')
            inline += previous.create_short_reference()
            paragraph += inline

        if next:
            inline = nodes.inline()
            inline['classes'] += ['next']
            inline += nodes.Text('Next: ')
            inline += next.create_short_reference()
            paragraph += inline
        
        breadcrumbs = self.create_short_breadcrumbs()
        if breadcrumbs:
            inline = nodes.inline()
            inline['classes'] += ['breadcrumbs']
            for breadcrumb in breadcrumbs:
                inline += breadcrumb
                inline += nodes.Text(u' \u00bb ')
            inline += nodes.Text(shorten(self.title))
            paragraph += inline

        header = navigation.deepcopy()
        header['classes'] += ['navigation-header']
        self.document.insert(0, header)

        footer = navigation.deepcopy()
        footer['classes'] += ['navigation-footer']
        self.document += footer

    def create_breadcrumbs(self):
        if self.parent:
            return (self.parent.create_breadcrumbs() +
                    [self.parent.create_reference()])
        else:
            return []

    def create_short_breadcrumbs(self):
        if self.parent:
            return (self.parent.create_short_breadcrumbs() +
                    [self.parent.create_short_reference()])
        else:
            return []

    def create_reference(self):
        ref = nodes.reference()
        ref['refuri'] = self.filename
        ref['name'] = self.title
        ref += nodes.Text(self.title)
        return ref

    def create_short_reference(self):
        ref = nodes.reference()
        ref['refuri'] = self.filename
        ref['name'] = self.title
        ref['title'] = self.title
        ref += nodes.Text(shorten(self.title))
        return ref

    def preorder(self):
        yield self
        for child in self.children:
            for c in child.preorder():
                yield c

class PythonColorizer(HTMLDoctestColorizer):
    strong_re = re.compile('(.*)\*\*STRONG_LINE\*\*')

    def colorize_codeblock(self, s):
        text = HTMLDoctestColorizer.colorize_codeblock(self, s)
        text = self.strong_re.sub(self.sub_strong_line, text)
        return text

    def sub_strong_line(self, match):
        return '<strong>%s</strong>' % match.group(1)

    def markup(self, s, tag):
        if tag == 'comment' and s[1:].strip() == '***':
            return '**STRONG_LINE**'
        return HTMLDoctestColorizer.markup(self, s, tag)

def gendoc_html(input_file, html_dir, api_objects, options):
    input_dir = os.path.dirname(input_file)
    files = []
    titles = {}

    # XXX Should calculate how apidoc_dir is relative to html_dir...
    apidoc_dir_rel = '../api' 

    # Read root doctree
    doctree = publish_doctree(open(input_file).read(), source_path=input_file)

    # Convert images
    for image in [n for n in doctree.traverse() if isinstance(n, nodes.image)]:
        uri = image.attributes['uri']
        image.attributes['uri'] = convert_image(uri, input_dir, html_dir)

    # Colorize literal blocks
    for block in [n for n in doctree.traverse() \
                  if (isinstance(n, nodes.literal_block))]:
        # Use "plain" class on literal blocks to disable syntax coloring,
        # e.g.:
        #
        # .. class:: plain
        #
        #   ::
        #
        #     Plain text goes here.
        #
        if 'plain' not in block.attributes['classes']:
            pysrc = block.astext()
            html = PythonColorizer().colorize_codeblock(pysrc)
            raw = nodes.raw(text=html, format='html')
            block.replace_self(raw)

    # Recursively split sections down to depth N into separate doctrees
    root_filename = os.path.splitext(os.path.basename(input_file))[0]
    root_page = Page(doctree, 
                     '%s.html' % root_filename,
                     None, [])
    if options.depth:
        root_page.split(options.depth)

    # Add refuri to all references that use refid, to point to the
    # appropriate page.
    id_map = {} # Map id of nodes to uri
    root_page.collect_ids(id_map)
    # Only works for explicit section links; see future uses of id_map
    root_page.add_refuri(id_map) 

    # Get page connectivity and add navigation
    pages = [n for n in root_page.preorder()]
    if options.add_navigation:
        for i, page in enumerate(pages):
            if i > 0:
                previous = pages[i - 1]
            else:
                previous = None
            if i + 1 < len(pages):
                next = pages[i + 1]
            else:
                next = None
            page.add_navigation(previous, next)


    for page in pages:
        # Resolve links
        linked_objects = set()
        for ref in [n for n in page.document.traverse() \
                    if isinstance(n, nodes.title_reference)]:
            title = ref.astext()
            url = None
            if title.endswith('.py'):
                # Copy in referenced example program and link.
                shutil.copy(title, html_dir)
                url = os.path.basename(title)
                canonical = title
                link_class = 'filelink'
            elif title in api_objects and api_objects[title][0]:
                # Link to API page
                canonical, uri = api_objects[title]
                url = os.path.join(apidoc_dir_rel, uri)
                link_class = 'apilink'
            elif title.lower().replace(' ', '-') in id_map:
                # Section link (using `xx` instead of `xx`_).
                canonical = title
                url = id_map[title.lower().replace(' ', '-')]
                link_class = 'sectionlink'

            # Only link once per page, to avoid littering the text
            # with too many links
            if url and url not in linked_objects:
                linked_objects.add(url)

                newref = nodes.reference()
                newref.children = [c.deepcopy() for c in ref.children]
                newref['refuri'] = url
                if canonical != title:
                    newref['title'] = canonical # tooltip is canonical name
                if link_class:
                    newref['link_class'] = link_class
                ref.replace_self(newref)

        # Write page
        settings = {
            'embed_stylesheet': False,
            'stylesheet': 'doc.css',
            'stylesheet_path': None,
        }
        writer = HTMLWriter()
        html = publish_from_doctree(page.document, 
                                    writer=writer,
                                    settings_overrides=settings)
        output_file = open(os.path.join(html_dir, page.filename), 'w')
        output_file.write(html)

def get_api_objects(apidoc_dir):
    '''Return a dict of name -> (canonical, uri) of api_objects exported from
    epydoc.'''
    objects = {}

    # Read API doc objects
    apidoc_file = open(os.path.join(apidoc_dir, 'api-objects.txt'))
    for line in apidoc_file:
        name, url = line.split('\t')

        # Canonical name always matches
        objects[name] = (name, url)
        canonical = name
        # Also strip off leading components one at a time and add if not
        # ambiguous
        while '.' in name:
            name = name.split('.', 1)[1]
            if name in objects and (canonical, url) != objects[name]:
                objects[name] = (None, None) # Ambiguous: don't match
            else:
                objects[name] = (canonical, url)

    return objects


if __name__ == '__main__':
    op = optparse.OptionParser()
    op.add_option('--apidoc-dir')
    op.add_option('--html-dir')
    op.add_option('--depth', type='int')
    op.add_option('--add-navigation', action='store_true')
    options, args = op.parse_args()

    if options.apidoc_dir:
        api_objects = get_api_objects(options.apidoc_dir)
    else:
        api_objects = {}

    for input_file in args:
        gendoc_html(input_file, options.html_dir, api_objects, options)
