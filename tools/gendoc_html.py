#!/usr/bin/env python
# $Id:$

import optparse
import os
import os.path
import subprocess

from docutils.core import publish_doctree, publish_from_doctree
from docutils.utils import new_document
from docutils import nodes

from epydoc.markup.doctest import HTMLDoctestColorizer

def convert_image(uri, input_dir, html_dir):
    '''Convert image found at uri in input_dir to something useable and place
    in html_dir.  Return the new uri.'''

    # Bail if it's external
    if uri.startswith('http:'):
        return uri

    # Simple image conversion using ImageMagick (must be in path)
    if uri.endswith('.svg'):
        newuri = '%s.png' % os.path.splitext(os.path.basename(uri))[0]
        input_file = os.path.join(input_dir, uri)
        output_file = os.path.join(html_dir, newuri)
        subprocess.call('convert %s %s' % (input_file, output_file),
                        shell=True)
        return newuri

def gendoc_html(apidoc_dir, input_dir, html_dir):
    files = []
    titles = {}
    objects = {}

    # Read API doc objects
    apidoc_file = open(os.path.join(apidoc_dir, 'api-objects.txt'))
    for line in apidoc_file:
        name, url = line.split('\t')
        # Canonical name always matches
        objects[name] = url
        # Also strip off leading components one at a time and add if not
        # ambiguous
        while '.' in name:
            name = name.split('.', 1)[1]
            if name in objects and url != objects[name]:
                objects[name] = None # Ambiguous: don't match
            else:
                objects[name] = url

    # XXX Should calculate how apidoc_dir is relative to html_dir...
    apidoc_dir_rel = 'api' 

    # Read sources
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            output_filename = '%s.html' % os.path.splitext(filename)[0]
            file = open(os.path.join(input_dir, filename))
            doctree = publish_doctree(file.read())
            title = doctree[doctree.first_child_matching_class(nodes.Titular)]
            titles[title.astext().lower()] = output_filename
            files.append((output_filename, doctree))

    # Mangle each doctree
    for output_filename, doctree in files:
        # Resolve links
        linked_objects = set()
        for ref in [n for n in doctree.traverse() \
                    if isinstance(n, nodes.title_reference)]:
            title = ref.astext()
            url = None
            if title.lower() in titles:
                url = titles[title.lower()]
            elif title in objects and objects[title]:
                url = os.path.join(apidoc_dir_rel, objects[title])
                # Only link once per document, to avoid littering the text
                # with too many links
                if url in linked_objects:
                    url = None
                linked_objects.add(url)
            if url:
                newref = nodes.reference()
                newref.children = [c.deepcopy() for c in ref.children]
                newref.attributes['refuri'] = url
                ref.replace_self(newref)

        # Convert images
        for image in [n for n in doctree.traverse() \
                      if isinstance(n, nodes.image)]:
            uri = image.attributes['uri']
            image.attributes['uri'] = convert_image(uri, input_dir, html_dir)

        # Colorize literal blocks
        for block in [n for n in doctree.traverse() \
                      if (isinstance(n, nodes.literal_block))]:
            pysrc = block.astext()
            html = HTMLDoctestColorizer().colorize_codeblock(pysrc)
            raw = nodes.raw(text=html, format='html')
            block.replace_self(raw)

    # Write out HTML files
    for output_filename, doctree in files:
        settings = {
            'embed_stylesheet': False,
            'stylesheet': 'doc.css',
            'stylesheet_path': None,
        }
        html = publish_from_doctree(doctree, 
                                    writer_name='html',
                                    settings_overrides=settings)
        output_file = open(os.path.join(html_dir, output_filename), 'w')
        output_file.write(html)

if __name__ == '__main__':
    op = optparse.OptionParser()
    op.add_option('--apidoc-dir')
    op.add_option('--input-dir')
    op.add_option('--html-dir')
    options, args = op.parse_args()

    gendoc_html(options.apidoc_dir, options.input_dir, options.html_dir)
