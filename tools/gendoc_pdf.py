#!/usr/bin/env python

'''Generate PDF documentation

Requires docutils, docbook XSL stylesheets, xsltproc and Apache FOP (with
Batik).
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import shutil
import subprocess
from xml.dom.minidom import parse

from docutils.core import publish_doctree, publish_from_doctree
from docutils.writers import docbook
from docutils import nodes

script_home = os.path.dirname(__file__)
doc_root = os.path.join(script_home, '../doc')

def get_docbook_path():
    '''Look up docbook URL in installed catalogs.  If you don't use catalogs,
    hack this function to return the complete path to your docbook dir.
    '''
    url = 'http://docbook.sourceforge.net/release/xsl/current/'
    if 'XML_CATALOG_FILES' in os.environ:
        catalogs = os.environ['XML_CATALOG_FILES'].split()
        for catalog in catalogs:
            proc = subprocess.Popen('xmlcatalog %s %s' % (catalog, url),
                                    shell=True,
                                    stdout=subprocess.PIPE)
            path = proc.communicate()[0]
            if proc.returncode == 0:
                return path.strip()

    raise "Docbook stylesheets not found...  hack me with a path."

def elements(node, name):
    '''Return all descendent element nodes of 'node' with given name'''
    matches = []
    if node.nodeType == node.ELEMENT_NODE and node.nodeName == name:
        matches = [node]
    for child in node.childNodes:
        matches += elements(child, name)
    return matches

def rest2docbook(rest_filename, docbook_filename):
    print 'Reading %s' % rest_filename

    input_dir = os.path.dirname(rest_filename)
    output_dir = os.path.dirname(docbook_filename)

    # Read rest doctree
    doctree = publish_doctree(open(rest_filename).read(),
                              source_path=rest_filename)

    # Remove fields (docbook writer ignores but warns)
    for field in [n for n in doctree.traverse() if isinstance(n, nodes.field)]:
        field.parent.remove(field)

    # Remove line nodes (docbook crashes on them)
    for line in [n for n in doctree.traverse() if isinstance(n, nodes.line)]:
        line.parent.replace(line, line.children)

    # Copy images
    for img in [n for n in doctree.traverse() if isinstance(n, nodes.image)]:
        img['scale'] = '50'
        srcfile = os.path.join(input_dir, img['uri'])
        destfile = os.path.join(output_dir, img['uri'])
        shutil.copyfile(srcfile, destfile)

    print 'Writing %s' % docbook_filename

    # Write docbook xml
    writer = docbook.Writer()
    settings = {
        'doctype': 'book',
    }
    docbook_xml = publish_from_doctree(doctree,     
                                   writer=writer,
                                   settings_overrides=settings)
    open(docbook_filename, 'w').write(docbook_xml)

    # Open docbook xml and fix it
    print 'Reading %s' % docbook_filename
    doc = parse(docbook_filename)

    # Strip leading newline from programlisting
    for elem in elements(doc, 'programlisting'):
        if elem.childNodes and elem.childNodes[0].nodeType == elem.TEXT_NODE:
            elem.childNodes[0].nodeValue = elem.childNodes[0].nodeValue.strip()

    # Dodgy hack to compensate for FOP's lack of table layout.
    # Programming guide tables need more room in the first (header) column than
    # right-hand columns.
    for elem in elements(doc, 'colspec'):
        if elem.getAttribute('colname') == 'col_1':
            elem.attributes['colwidth'] = '2*'
        else:
            elem.attributes['colwidth'] = '1*'

    # Strip table of contents (docbook creates its own)
    for title in elements(doc, 'title'):
        if title.childNodes[0].nodeType == title.TEXT_NODE and \
           title.childNodes[0].nodeValue == 'Contents':
            section = title.parentNode
            if section.nodeType == section.ELEMENT_NODE and \
               section.nodeName == 'section':
                section.parentNode.removeChild(section)

    # Strip local contents
    for section in elements(doc, 'section'):
        for child in section.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                break
        if child.nodeName == 'itemizedlist':
            section.parentNode.removeChild(section)

    # Pull everything before first chapter into a preface
    preface_nodes = []
    preface = doc.createElement('preface')
    preface_title = doc.createElement('title')
    preface_title.appendChild(doc.createTextNode('Welcome'))
    preface.appendChild(preface_title)
    for child in doc.documentElement.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            if child.nodeName == 'chapter':
                for node in preface_nodes:
                    doc.documentElement.removeChild(node)
                for node in preface_nodes:
                    preface.appendChild(node)
                doc.documentElement.insertBefore(preface, child)
                break
            elif child.nodeName != 'bookinfo':
                preface_nodes.append(child)

    # Scale screenshots of windows down (programming guide hack to fit in
    # table)
    for imagedata in elements(doc, 'imagedata'):
        fileref = imagedata.getAttribute('fileref')
        if fileref.startswith('window_xp_') or fileref.startswith('window_osx'):
            imagedata.attributes['scale'] = '25'

    # Write fixed docbook
    print 'Writing %s' % docbook_filename
    open(docbook_filename, 'w').write(doc.toxml())

def docbook2pdf(docbook_filename, pdf_filename):
    # Run docbook FO stylesheet to produce XSL:FO document
    stylesheet = os.path.join(get_docbook_path(), 'fo/docbook.xsl')
    fo_filename = '%s.fo.xml' % os.path.splitext(docbook_filename)[0] 

    print 'Using %s' % stylesheet
    print 'Writing %s' % fo_filename
    parameters = [
        #'--stringparam paper.type A4',
        #'--param double.sided 1',
        #'--stringparam alignment left',
        #'--param shade.verbatim 1',
        '--param chapter.autolabel 0',
    ]
    result = subprocess.call('xsltproc %s -o %s %s %s ' % (
        ' '.join(parameters), fo_filename, stylesheet, docbook_filename),
        shell=True)

    if result != 0:
        raise 'Aborting due to errors during docbook->FO conversion'

    print 'Writing %s' % pdf_filename
    subprocess.call('fop -fo %s -pdf %s' % (fo_filename, pdf_filename),
                    shell=True)

if __name__ == '__main__':
    try:
        os.makedirs(os.path.join(doc_root, 'pdf'))
    except OSError:
        pass
    try:
        os.makedirs(os.path.join(doc_root, 'docbook'))
    except OSError:
        pass
    rest2docbook(os.path.join(doc_root, 'programming_guide/index.txt'),
                 os.path.join(doc_root, 'docbook/programming_guide.xml'))
    docbook2pdf(os.path.join(doc_root, 'docbook/programming_guide.xml'),
                os.path.join(doc_root, 'pdf/programming_guide.pdf'))
