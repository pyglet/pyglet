#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import shutil
import sys
import time
from xml.dom.minidom import parse

try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree

def get_elem_by_id(doc, name, id):
    for element in doc.getElementsByTagName(name):
        if element.getAttribute('id') == id:
            return element

def element_children(parent, name):
    for child in parent.childNodes:
        if (child.nodeType == child.ELEMENT_NODE and
            child.nodeName == name):
            yield child

def element_text(elem):
    if elem.nodeType == elem.TEXT_NODE:
        return elem.nodeValue
    else:
        s = ''
        for child in elem.childNodes:
            s += element_text(child)
        return s

if __name__ == '__main__':
    root = os.path.join(os.path.dirname(__file__), '..')
    input_dir = os.path.join(root, 'website')
    output_dir = os.path.join(root, 'website/dist')
    template_filename = os.path.join(input_dir, 'template.xhtml')
    news_items_filename = os.path.join(input_dir, 'news-items.xml')
    exclude_files = ('template.xhtml', 'news-items.xml')

    try:
        os.makedirs(output_dir)
    except OSError:
        pass #exists

    # Read news items
    news_items_doc = parse(news_items_filename)
    news_items = [item for item in element_children(
                                    news_items_doc.documentElement, 'item')]

    # Write ATOM feed (news.xml)
    atom_filename = os.path.join(output_dir, 'news.xml')
    root = ElementTree.Element('feed', xmlns="http://www.w3.org/2005/Atom")
    SE = ElementTree.SubElement
    title = SE(root, 'title')
    title.text = 'Recent news from the pyglet project'
    SE(root, 'link', href='http://www.pyglet.org/')
    SE(root, 'link', rel='self', href='http://www.pyglet.org/news.xml')
    SE(root, 'id').text = 'http://www.pyglet.org/news/'

    date = time.strptime(news_items[0].getAttribute('date'), '%d-%B-%Y')
    date = time.strftime('%Y-%m-%d', date)
    SE(root, 'updated').text = "%sT00:00:00Z" % date
    for item in news_items[:10]:
        content = element_text(item)
        date = time.strptime(item.getAttribute('date'), '%d-%B-%Y')
        date = time.strftime('%Y-%m-%d', date)

        entry = SE(root, 'entry')
        author = SE(entry, 'author')
        SE(author, 'name').text = item.getAttribute('author')
        SE(entry, 'title').text = item.getAttribute('title')
        SE(entry, 'summary').text = content
        SE(entry, 'content').text = content
        SE(entry, 'updated').text = "%sT00:00:00Z" % date
        SE(entry, 'id').text='http://www.pyglet.org/news/' + date
    s = open(atom_filename, 'w')
    s.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
    ElementTree.ElementTree(root).write(s, 'utf-8')

    # Read template
    template = parse(template_filename)

    for file in os.listdir(input_dir):
        if file in exclude_files:
            continue
        if not file.endswith('.xml'):
            if os.path.isfile(os.path.join(input_dir, file)):
                shutil.copy(os.path.join(input_dir, file), output_dir)
            continue

        input_doc = parse(os.path.join(input_dir, file))
        output_doc = template.cloneNode(True)

        # Insert news items
        for news_elem in element_children(input_doc.documentElement, 'news'):
            count = None
            if news_elem.hasAttribute('items'):
                count = int(news_elem.getAttribute('items'))
            for item in news_items[:count]:
                author = item.getAttribute('author')
                date = item.getAttribute('date')

                p = input_doc.createElement('p')
                p.setAttribute('class', 'news-item')
                title = input_doc.createElement('span')
                title.setAttribute('class', 'news-title')
                title.appendChild(input_doc.createTextNode(
                    '%s.' % item.getAttribute('title')))
                p.appendChild(title)

                for child in item.childNodes:
                    p.appendChild(child.cloneNode(True))
                attribution = input_doc.createElement('span')
                attribution.setAttribute('class', 'news-attribution')
                attribution.appendChild(input_doc.createTextNode(
                    'Submitted by %s on %s.' % (author, date)))
                p.appendChild(attribution)
                news_elem.parentNode.insertBefore(p, news_elem)
            news_elem.parentNode.removeChild(news_elem)
            

        # Write body content
        output_content = get_elem_by_id(output_doc, 'div', 'content')
        for child in input_doc.documentElement.childNodes:
            output_content.appendChild(child.cloneNode(True))

        # Set class on active tab
        banner_tabs = get_elem_by_id(output_doc, 'div', 'banner-tabs')
        for child in element_children(banner_tabs, 'span'):
            if child.hasAttribute('select'):
                if child.getAttribute('select') == file:
                    child.setAttribute('class', 'selected')
                child.removeAttribute('select')

        output_filename = os.path.join(output_dir, 
                                       '%s.html' % os.path.splitext(file)[0])
        output_doc.writexml(open(output_filename, 'w'))
