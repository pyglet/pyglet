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
        'doctype': 'article',
    }
    docbook_xml = publish_from_doctree(doctree,     
                                   writer=writer,
                                   settings_overrides=settings)
    open(docbook_filename, 'w').write(docbook_xml)

def docbook2pdf(docbook_filename, pdf_filename):
    # Run docbook FO stylesheet to produce XSL:FO document
    stylesheet = os.path.join(get_docbook_path(), 'fo/docbook.xsl')
    fo_filename = '%s.fo.xml' % os.path.splitext(docbook_filename)[0] 

    print 'Using %s' % stylesheet
    print 'Writing %s' % fo_filename
    result = subprocess.call('xsltproc -o %s %s %s ' % (
        fo_filename, stylesheet, docbook_filename),
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
