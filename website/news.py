import os, datetime, operator, md5, StringIO
import cElementTree as ElementTree

# gather
entries = []
for name in os.listdir('news-items'):
    if not name.endswith('.txt'): continue
    info = {'id': os.path.splitext(name)[0], 'content': ''}
    entries.append(info)
    for line in open(os.path.join('news-items', name)):
        if line.startswith('date='):
            info['date'] = tuple(map(int, line[5:].split('-')))
        elif line.startswith('title='):
            info['title'] = line[6:].strip()
        elif line.startswith('author='):
            info['author'] = line[7:].strip()
        else:
            info['content'] += line

entries.sort(key=operator.itemgetter('date'))
entries.reverse()

def save_file(filename, content):
    if os.path.exists(filename):
        m = md5.new()
        m.update(open(filename, 'r').read())
        dig = m.digest()
        m = md5.new()
        m.update(content)
        write = m.digest() != dig
    else:
        write = True
    if write:
        print 'Writing', filename
        open(filename, 'w').write(content)

# write HTML
html = ['''<table id="news" align="center">
<tbody><tr><th colspan="2">NEWS:</th></tr>''']
row = '<tr><td class="first">%s:<br><em>%s</em></td><td>%s</td></tr>'
for entry in entries[:10]:
    content = '<br>'.join(filter(None, ['<strong>%s</strong>'%entry['title'],
        entry['content']]))
    html.append(row%('%d-%d-%d'%entry['date'], entry['author'], content))
html.append('</tbody></table>')
save_file('news.php', '\n'.join(html))

# XXX write archive

# write ATOM
root = ElementTree.Element('feed', xmlns="http://www.w3.org/2005/Atom")
SE = ElementTree.SubElement
title = SE(root, 'title')
title.text = 'Recent news from the pyglet project'
SE(root, 'link', href='http://www.pyglet.org/')
SE(root, 'id').text = 'http://www.pyglet.org/news/'
SE(root, 'updated').text = "%4d-%02d-%02dT00:00:00Z"%entries[0]['date']
for info in entries[:10]:
    entry = SE(root, 'entry')
    author = SE(entry, 'author')
    SE(author, 'name').text = info['author']
    SE(entry, 'title').text = info['title']
    SE(entry, 'summary').text = info['content'] or info['title']
    SE(entry, 'content').text = info['content'] or info['title']
    SE(entry, 'updated').text = "%4d-%02d-%02dT00:00:00Z"%info['date']
    SE(entry, 'id').text='http://www.pyglet.org/news/' + info['id']
s = StringIO.StringIO()
s.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
ElementTree.ElementTree(root).write(s, 'utf-8')
content = s.getvalue()
save_file('news.xml', content)

