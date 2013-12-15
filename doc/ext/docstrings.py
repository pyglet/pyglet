# -*- coding: utf-8 -*-
''' pyglet specific docstring transformations.
'''

_debug = False

def debug(lines):
    with open('debug.log', 'a') as f:
        for line in lines:
            f.write(line+"\n")

if _debug:
    with open('debug.log', 'w') as f:
        f.write("Docstring modifications.\n\n")


def indentation(line):
    if line.strip()=="": return 0
    return len(line) - len(line.lstrip())


def process_block(converter, lines, start):
    ''' Apply a transformation to an indented block
    '''
    first = indentation(lines[start])
    current = first
    blocks = [[]]
    block = 0

    for i, line in enumerate(lines[start+1:]):
        level = indentation(line)
        if level<=first:
            try: # allow one blank line in the block
                if line.strip()=="" and \
                   (current == indentation(lines[start + i + 2])):
                    continue
            except: pass
            break
        if level<current:
            blocks.append([line])
            block += 1    
        else:
            blocks[block].append(line) 
        current = level

    result = []
    for block in blocks:
            result += converter(block)

    return i, result


def ReST_parameter(lines):
    ''' Converts :parameters: blocks to :param: markup
    '''
    indent = indentation(lines[0])
    part = lines[0].replace("`","").split(":")
    name = part[0].replace(" ", "")
    rest = [":param "+name+":"]
    for line in lines[1:]:
        rest.append(line[indent:])
    if len(part)>1:
        rest.append(":type "+name+": "+part[1].strip().lstrip())
    return rest


def ReST_Ivariable(lines):
    ''' Converts :Ivariable: blocks to :var: markup
    '''
    indent = indentation(lines[0])
    part = lines[0].replace("`","").split(":")
    name = part[0].replace(" ", "")
    rest = [":var "+name+":"]
    for line in lines[1:]:
        rest.append(line[indent:])
    if len(part)>1:
        rest.append(":type "+name+": "+part[1].strip().lstrip())
    return rest




def modify_docstrings(app, what, name, obj, options, lines,
                      reference_offset=[0]):

    original = lines[:]

    def convert(converter, start):
        affected, result = process_block(converter, lines, start)
        for x in range(start, start+affected+1):
            del lines[start]
        for i, line in enumerate(result):
            lines.insert(start+i, line)

    i=0
    while i<len(lines):
        line = lines[i]
        if ":parameters:" in line.lower():
            convert(ReST_parameter, i)
            
        elif ":Ivariables:" in line:
            convert(ReST_Ivariable, i)

        elif ":guide:" in line:
            lines[i] = lines[i].replace(u':guide:`',
                        u'.. seealso:: Programming Guide - :ref:`guide_')
            
        elif ":deprecated:" in line:
            lines[i] = lines[i].replace(u':deprecated:',
                                u'.. warning:: Deprecated.')
            lines.insert(i,"")
            lines.insert(i,"")

        elif line.strip().startswith(":since:"):
            lines[i] = lines[i].replace(u':since:',
                                u'.. note:: Since')
            lines.insert(i+1,"")
            lines.insert(i,"")
            
        elif line.strip().startswith("**since:**"):
            lines[i] = lines[i].replace(u'**since:**',
                                u'.. note:: Since')
            lines.insert(i+1,"")
            lines.insert(i,"")
            
        elif ":event:" in line.lower():
            lines[i] = lines[i].replace(u':event:', u'.. event mark')

        i += 1

            
    if _debug and original!=lines:
        title = what + " " +name
        debug(["\n",title, "-"*len(title)])
        debug(["Original:", ""]+original)
        debug(["Redacted:", ""]+lines)
            

def setup(app):
    app.connect('autodoc-process-docstring', modify_docstrings)
