#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from StringIO import StringIO
import warnings

from Plex import *
from Plex.Traditional import re

from pyglet.layout.base import *

class SelectableElement(object):
    '''Elements must implement this interface to allow CSS selectors to
    traverse them.
    '''
    parent = None               # SelectableElement
    previous_sibling = None     # SelectableElement
    attributes = None           # dict
    id = None                   # str
    classes = None              # list
    name = None                 # str

    def short_repr(self):
        s = self.name
        if self.id:
            s += '#%s' % self.id
        for c in self.classes or []:
            s += '.%s' % c
        return s

    def __repr__(self, short=False):
        s = self.short_repr()
        for key, value in self.attributes.items():
            if key != 'id':
                s += '[%s=%r]' % (key, value)
        if self.parent:
            s += '(parent=%s)' % self.parent.short_repr()
        if self.previous_sibling:
            s += '(previous_sibling=%s)' % self.previous_sibling.short_repr()
        return s

class Stylesheet(object):
    def __init__(self, data):
        if not hasattr(data, 'read'):
            data = StringIO(data)
        scanner = Scanner(lexicon, data)
        parser = Parser(scanner)
        charset, imports, rules = parser.stylesheet()

        self.rules = rules      # only for debugging

        self.names = {}
        self.ids = {}
        self.classes = {}
        self.universals = []

        for rule in rules:
            primary = rule.selector.primary
            if primary.name:
                if primary.name not in self.names:
                    self.names[primary.name] = []
                self.names[primary.name].append(rule)
            elif primary.id:
                if primary.id not in self.ids:
                    self.ids[primary.id] = []
                self.ids[primary.id].append(rule)
            elif primary.classes:
                if primary.classes[0] not in self.classes:
                    self.classes[primary.classes[0]] = []
                self.classes[primary.classes[0]].append(rule)
            else:
                self.universals.append(rule)

    def get_declarations(self, elem):
        # Quickly get some starting points.
        primaries = []
        primaries += self.names.get(elem.name, [])
        if elem.id:
            primaries += self.ids.get(elem.id, [])
        for c in elem.classes or []:
            primaries += self.classes.get(c, [])
        primaries += self.universals

        # Filter out non-matching
        matches = [rule for rule in primaries if self.matches(rule, elem)]

        # Order by specifity
        matches.sort(lambda a,b: a.specifity - b.specifity)

        declarations = []
        for rule in matches:
            declarations += rule.declarations
        return declarations

    def matches(self, rule, elem):
        if not rule.selector.primary.matches(elem):
            return False

        for selector in rule.selector.combiners:
            if selector.combinator == '>':
                elem = elem.parent
            elif selector.combinator == '+':
                elem = elem.previous_sibling
            else:
                elem = elem.parent
                while elem:
                    if selector.simple.matches(elem):
                        break
                    elem = elem.parent
                else:
                    return False
                continue
            if not elem:
                return False
            if not selector.simple.matches(elem):
                return False

        return True

    def pprint(self):
        for rule in self.rules:
            rule.pprint()

class Import(object):
    def __init__(self, location, media):
        self.location = location
        self.media = media

    def pprint(self):
        print '@import', self.location, ','.join(self.media)

class Page(object):
    def __init__(self, pseudo, declarations):
        self.pseudo = pseudo
        self.declarations = declarations

class Rule(object):
    media = None

    def __init__(self, selector, declarations):
        self.selector = selector
        self.declarations = declarations

        # Specifity calculated according to 6.4.3 with base 256
        specifity = 0
        simples = [selector.primary] + [s.simple for s in selector.combiners]
        for s in simples:
            if s.id:
                specifity += 1 << 16
            specifity += (1 << 8) * (len(s.classes) + len(s.attribs))
            if s.name:
                specifity += 1
        self.specifity = specifity

    def is_media(self, media):
        return (self.media is None or
                'all' in self.media or 
                media in self.media)

    def pprint(self):
        if self.media:
            print '@media', ','.join(self.media), '{', 
        self.selector.pprint()
        print '{'
        for declaration in self.declarations:
            print declaration, ';'
        print '}'

class Selector(object):
    def __init__(self, primary, combiners):
        self.primary = primary
        self.combiners = combiners

    def pprint(self):
        print 'Selector(primary=%r,combiners=%r)' % \
            (self.primary, self.combiners),

class SimpleSelector(object):
    def __init__(self, name, id, classes, attribs, pseudos):
        self.name = name
        self.id = id
        self.classes = classes
        self.attribs = attribs
        self.pseudos = pseudos

    def __repr__(self):
        s = self.name or '*'
        if self.id:
            s += '#%s' % self.id
        for c in self.classes:
            s += '.%s' % c
        for a in self.attribs:
            s += repr(a)
        for p in self.pseudos:
            s += repr(p)
        return s

    def matches(self, elem):
        if self.name is not None and elem.name != self.name:
            return False
        if self.id is not None and elem.id != self.id:
            return False
        for c in self.classes:
            if c not in elem.classes:
                return False
        for attr in self.attribs:
            if attr not in elem.attributes:
                return False
            value = elem.attributes[attr]
            if attr.op == '=' and value != attr.value:
                return False
            elif attr.op == '~=' and attr.value not in value.split():
                return False
            elif attr.op == '|=':
                pre = attr.value.split('-')
                if value.split('-')[:len(pre)] != pre:
                    return False
        return True
        
class CombiningSelector(object):
    def __init__(self, combinator, simple):
        self.combinator = combinator
        self.simple = simple

    def __repr__(self):
        return '%s%r' % (self.combinator or '', self.simple)

class Attrib(object):
    def __init__(self, name, op, value):
        self.name = name
        self.op = op
        self.value = value

    def __repr__(self):
        if self.op:
            return '[%s%s%s]' % (self.name, self.op, self.value)
        else:
            return '[%s]'

class Pseudo(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return ':%s' % self.name

class PseudoFunction(Pseudo):
    def __init__(self, name, param):
        super(PseudoFunction, self).__init__(name)
        self.param = param

    def __repr__(self):
        return ':%s(%s)' % (self.name, self.param)

class Declaration(object):
    def __init__(self, property, values, priority):
        self.property = property
        self.values = values
        self.priority = priority

    def __repr__(self):
        s = '%s: %r' % (self.property, self.values)
        if self.priority:
            s += ' ! important'
        return '%s(%s)' % (self.__class__.__name__, s)


# Macros
nonascii = re('[^\0-\177]')
_h = NoCase(re('[0-9a-f]'))
_unicode_num = _h + Opt(_h + Opt(_h + Opt(_h + Opt(_h + Opt(_h)))))
unicode = \
   (Str('\\') + _unicode_num + Opt(Str('\r\n') | Any(' \n\r\t\f')))
escape = unicode | (Str('\\') + NoCase(re('[^\n\r\f0-9a-f]')))
nmstart = NoCase(re('[_a-z]')) | nonascii | escape
nmchar = NoCase(re('[_a-z0-9-]')) | nonascii | escape
name = Rep1(nmchar)
ident = Opt(Str('-')) + nmstart + Rep(nmchar)
num = re('[0-9]+') | re('[0-9]*\\.[0-9]+')
nl = Str('\n') | Str('\r\n') | Str('\r') | Str('\f')
string1 = (Str('"') + 
           Rep(AnyBut('\n\r\f\\"') | (Str('\\') + nl) | escape) + 
           Str('"'))
string2 = (Str("'") + 
           Rep(AnyBut("\n\r\f\\'") | (Str('\\') + nl) | escape) + 
           Str("'"))
string = string1 | string2
invalid1 = (Str('"') + 
           Rep(AnyBut('\n\r\f\\"') | (Str('\\') + nl) | escape))
invalid2 = (Str("'") + 
           Rep(AnyBut("\n\r\f\\'") | (Str('\\') + nl) | escape))
invalid = invalid1 | invalid2
w = Rep(Any(' \t\r\n\f'))

# Tokens
IDENT = ident
ATKEYWORD = Str('@') + ident
STRING = string
HASH = Str('#') + name
NUMBER = num
PERCENTAGE = num + Str('%')
DIMENSION = num + ident
URI = (NoCase(Str('url(')) + w + string + w + Str(')')) | \
      (NoCase(Str('url(')) + w + 
       Rep(Any('!#$%&*-~')|nonascii|escape) + w + Str(')'))
UNICODE_RANGE = NoCase(Str('U+')) + _unicode_num + Opt(Str('-') + _unicode_num)
CDO = Str('<!--')
CDC = Str('-->')
S = Rep1(Any(' \t\r\n\f'))
COMMENT = re(r'/\*[^*]*\*+([^/*][^*]*\*+)*/')
FUNCTION = ident + Str('(')
INCLUDES = Str('~=')
DASHMATCH = Str('|=')
DELIM = AnyBut('\'"')
IMPORTANT = NoCase(Str('important'))

lexicon = Lexicon([
    (IDENT, lambda s,t: Ident(t)),
    (ATKEYWORD, lambda s,t: AtKeyword(t)),
    (STRING, lambda s,t: String(t)),
    (HASH, lambda s,t: Hash(t)),
    (NUMBER, lambda s,t: Number(t)),
    (PERCENTAGE, lambda s,t: Percentage(t)),
    (DIMENSION, lambda s,t: Dimension(t)),
    (URI, lambda s,t: URI(t)),
    (UNICODE_RANGE, lambda s,t: UnicodeRange(t)),
    (CDO, lambda s,t: CDO()),
    (CDC, lambda s,t: CDC()),
    (S, lambda s,t: Whitespace()),
    (COMMENT, IGNORE),
    (FUNCTION, lambda s,t: Function(t)),
    (INCLUDES, lambda s,t: Delim(t)),
    (DASHMATCH, lambda s,t: Delim(t)),
    (DELIM, lambda s,t: Delim(t)),
    (IMPORTANT, lambda s,t: Important())
])


class ParserException(Exception):
    def __init__(self,  file, line, col):
        self.file = file
        self.line = line
        self.col = col

    def __str__(self):
        return 'Parse error in "%s" at line %d, column %d' % \
            (self.file, self.line, self.col)

class UnexpectedToken(ParserException):
    pass

class Parser(object):
    def __init__(self, scanner):
        self._scanner = scanner
        self._lookahead = None

    def _read(self, *_types):
        if self._lookahead is not None:
            r = self._lookahead
            self._lookahead = None
        else:
            r = self._scanner.read()[0]
        if _types and r.__class__ not in  _types and r not in _types:
            raise UnexpectedToken(*self._scanner.position())
        return r

    def _peek(self):
        if self._lookahead is None:
            self._lookahead = self._scanner.read()[0]
        return self._lookahead

    def _is(self, *_types):
        peek = self._peek()
        return peek is not None and (peek.__class__ in _types or peek in _types)

    def _eat_whitespace(self):
        while self._is(Whitespace):
            self._read()

    # Productions
    # See Appendix G.1
    # -----------------------------------------------------------------------

    def stylesheet(self):
        # [ CHARSET_SYM STRING ';']?
        # [S|CDO|CDC]* [ import [S|CDO|CDC]* ]*
        # [ [ ruleset | media | page ] [S|CDO|CDC]* ]*
        charset = None
        if self.is_charset():
            charset = self.charset()
        while self._is(CDO, CDC, Whitespace):
            self._read()
        imports = []
        while self.is_import():
            imports.append(self.import_())
            while self._is(CDO, CDC, Whitespace):
                self._read()

        rules = []
        while True:
            if self.is_page():
                self.page()
                # Pages are current ignored
            elif self.is_media():
                rules += self.media()
            elif self.is_ruleset():
                rules += self.ruleset()
            else:
                break

            while self._is(CDO, CDC, Whitespace):
                self._read()
        
        return charset, imports, rules

    def is_charset(self):
        t = self._peek()
        return isinstance(t, AtKeyword) and t == '@charset'

    def charset(self):
        # charset : CHARSET_SYM STRING ';'
        self._read(AtKeyword)
        charset = self._read(String)
        self._read(';')
        return charset

    def medium_list(self):
        # medium_list : IDENT S* [ COMMA S* IDENT S*]*
        # (Not in CSS grammar, but common to media and import productions)
        media = []
        media.append(self._read(Ident))
        self._eat_whitespace()
        while self._is(','):
            self._eat_whitespace()
            media.append(self._read(Ident))
            self._eat_whitespace()
        return media

    def is_import(self):
        t = self._peek()
        return isinstance(t, AtKeyword) and t == '@import'

    def import_(self):
        # import : IMPORT_SYM S* [STRING|URI] S* [ medium_list ]? ';' S*
        self._read(AtKeyword)
        self._eat_whitespace()
        loc = self._read(String, URI)
        self._eat_whitespace()
        if self._is(Ident):
            media = self.medium_list()
        else:
            media = []
        self._read(';')
        return Import(loc, media)

    def is_page(self):
        t = self._peek()
        return isinstance(t, AtKeyword) and t == '@page'

    def page(self):
        # page : PAGE_SYM S* pseudo_page? S*
        #        LBRACE S* declaration [ ';' declaration ]* '}' S*
        self._read(AtKeyword)
        self._eat_whitespace()
        if self._is(':'):
            self._read()
            pseudo = self._read(Ident)
        self._eat_whitespace()
        self._read('{')
        declarations = self.declaration_list()
        self._read('}')
        self._eat_whitespace()
        return Page(pseudo, declarations)

    def is_media(self):
        t = self._peek()
        return isinstance(t, AtKeyword) and t == '@media'

    def media(self):
        # media : MEDIA_SYM S* medium_list LBRACE S* ruleset* '}' S*
        self._read(AtKeyword)
        self._eat_whitespace()
        media = self.medium_list()
        self._read('{')
        self._eat_whitespace()
        rules = []
        while self.is_ruleset():
            ruleset = self.ruleset()
            for rule in ruleset:
                rule.media = media
            rules += ruleset
        self._read('}')
        self._eat_whitespace()
        return rules

    def is_operator(self):
        return self._is('/', ',')

    def operator(self):
        # operator: '/' S* | COMMA S* | /* empty */
        # (empty production isn't matched here, see expr)
        op = self._read()
        self._eat_whitespace()
        return op

    def combinator(self):
        combinator = None
        if self._is('+', '>'):
            combinator = self._read()
        self._eat_whitespace()
        return combinator

    def is_unary_operator(self):
        return self._is('+', '-')

    def unary_operator(self):
        # unary_operator : '-' | PLUS
        if self._read('+', '-') == '-':
            return -1
        return 1

    def is_property(self):
        return self._is(Ident)

    def property(self):
        # property : IDENT S*
        prop = self._read(Ident)
        self._eat_whitespace()
        return prop

    def is_ruleset(self):
        return self.is_selector()

    def ruleset(self):
        # ruleset : selector [ COMMA S* selector ]*
        #           LBRACE S* declaration [ ';' S* declaration ]* '}' S*
        selectors = [self.selector()]
        while self._is(','):
            self._read()
            self._eat_whitespace()
            selectors.append(self.selector())
        self._read('{')
        self._eat_whitespace()
        declarations = self.declaration_list()
        self._read('}')
        self._eat_whitespace()

        return [Rule(s, declarations) for s in selectors]

    def is_selector(self):
        return self._is(Ident, '*', Hash, '.', '[', ':')

    def selector(self):
        # selector : simple_selector [ combinator simple_selector ]*
        combiners = []
        simple = self.simple_selector()
        while self._is('+', '>', Ident, '*', Hash, '.', '[', ':'):
            combinator = self.combinator()
            combiners.insert(0, CombiningSelector(combinator, simple))
            simple = self.simple_selector()
        
        return Selector(simple, combiners)

    def simple_selector(self):
        # simple_selector : element_name [ HASH | class | attrib | pseudo ]*
        #                 | [ HASH | class | attrib | pseudo ]+
        name = id = None
        attribs = []
        classes = []
        pseudos = []
        if self._is(Ident):
            name = self._read()
        elif self._is('*'):
            self._read()

        while True:
            if self._is(Hash):
                id = self._read()  # more than 1 id? too bad (css unspecified)
            elif self._is('.'):
                self._read()
                classes.append(self._read(Ident))
            elif self._is('['):
                attribs.append(self.attrib())
            elif self._is(':'):
                pseudos.append(self.pseudo())
            else:
                break

        # Not in spec but definitely required.
        self._eat_whitespace()

        return SimpleSelector(name, id, classes, attribs, pseudos)

    def attrib(self):
        # attrib : '[' S* IDENT S* [ [ '=' | INCLUDES | DASHMATCH ] S*
        #          [ IDENT | STRING ] S* ]? ']'
        self._read('[')
        self._eat_whitespace()
        name = self._read(Ident)
        self._eat_whitespace()
        op = value = None
        if self._is('=', '~=', '|='):
            op = self._read()
            self._eat_whitespace()
            value = self._read(Ident, String)
            self._eat_whitespace()
        self._read(']')
        return Attrib(name, op, value)

    def pseudo(self):
        # pseudo : ':' [ IDENT | FUNCTION S* IDENT? S* ')' ]
        self._read(':')
        if self._is(Ident):
            return Pseudo(self._read())
        else:
            name = self._read(Function)
            self._eat_whitespace()
            param = None
            if self._is(Ident):
                param = self._read(Ident)
                self._eat_whitespace()
            self._read(')')
            return PseudoFunction(name, param)

    def declaration_list(self):
        # declaration_list : S* declaration [';' S* declaration ]*
        # Adapted from bracketed section of ruleset; this is the start
        # production for parsing the style attribute of HTML/XHTML.
        # Declaration can also be empty, handle this here.
        self._eat_whitespace()
        declarations = []
        while self._is(Ident, ';'):
            if self._is(Ident):
                try:
                    declarations.append(self.declaration())
                except ParserException:
                    pass
                if not self._is(';'):
                    break
            self._read(';')
            self._eat_whitespace()
        return declarations

    def is_declaration(self):
        return self.is_property()

    def declaration(self):
        # declaration : property ':' S* expr prio? | /* empty */
        # Empty production of declaration is not handled here, see
        # declaration_list.
        prop = self.property()
        self._read(':')
        self._eat_whitespace()
        expr = self.expr()
        priority = None
        if self.is_prio():
            priority = self.prio()
        return Declaration(prop, expr, priority)

    def is_prio(self):
        return self._is('!')
    
    def prio(self):
        # prio : IMPORTANT_SYM S*
        self._read('!')
        self._eat_whitespace()
        self._read(Important)
        self._eat_whitespace()
        return 'important'

    def expr(self):
        # expr : term [ operator term ]*
        # operator is optional, implemented here not in operator.
        terms = []
        terms.append(self.term())
        while self.is_operator() or self.is_term():
            if self.is_operator():
                terms.append(self.operator())
            terms.append(self.term())
        return terms

    def is_term(self):
        return (self.is_unary_operator() or 
                self.is_function() or
                self.is_hexcolor() or
                self._is(Number, Percentage, Dimension, String, Ident, URI))

    def term(self):
        # term : unary_operator? [ NUMBER S* | PERCENTAGE S* | DIMENSION S* ]
        #        | STRING S* | IDENT S* | URI S* | hexcolor | function 
        if self.is_unary_operator():
            un = self.unary_operator()
            value = self._read(Number, Percentage, Dimension)
            if un == -1:
                value = -value
            self._eat_whitespace()
            return value
        if self.is_function():
            return self.function()
        elif self.is_hexcolor():
            return self.hexcolor()
        value = self._read(Number, Percentage, Dimension, String, Ident, URI)
        self._eat_whitespace()
        return value

    def is_function(self):
        return self._is(Function)

    def function(self):
        # function : FUNCTION S* expr ')' S*
        name = self._read()[:-1]
        position = self._scanner.position()
        self._eat_whitespace()
        args = self.expr()
        self._read(')')
        self._eat_whitespace()
        if name == 'rgb':
            if len(args) != 5 or args[1] != ',' or args[3] != ',':
                raise ParserException(*position)
            def component(c):
                if c.__class__ is Percentage:
                    return max(min(c / 100., 1.), 0.)
                elif c.__class__ is Number:
                    return max(min(c / 255., 1.), 0.)
                else:
                    raise ParserException(*position)
            r = component(args[0])
            g = component(args[2])
            b = component(args[4])
            return Color(r,g,b)
        else:
            raise ParserException(*position)

    def is_hexcolor(self):
        return self._is(Hash)

    def hexcolor(self):
        # hexcolor : HASH S*
        hash = self._read(Hash)
        if len(hash) not in (3, 6):
            raise ParserException(*self._scanner.position())
        self._eat_whitespace()
        return Color.from_hex(hash)

class ValidationException(Exception):
    pass

def _parse_generic(*args):
    # Accept any given type or ident.
    def f(value, render_device):
        if type(value) in args or \
           (type(value) in (Ident, Number) and value in args):
            return value
        else:
            raise ValidationException()
    return f

def _parse_shortcut(value_parser):
    # Parse shortcut properties that depend on the number of arguments:
    # 1: top/right/bottom/left
    # 2: top/bottom left/right
    # 3: top, left/right, bottom
    # 4: top, right, bottom, left
    def f(value, render_device):
        value = [value_parser(v, render_device) for v in value]
        if len(value) == 1:
            return value[0], value[0], value[0], value[0]
        elif len(value) == 2:
            return value[0], value[1], value[0], value[1]
        elif len(value) == 3:
            return value[0], value[1], value[2], value[1]
        elif len(value) == 4:
            return value
        else:
            raise ValidationException()
    return f

def _parse_color(value, render_device):
    if isinstance(value, Ident):
        if value in Color.names:
            return Color.names[value]
        else:
            raise ValidationException()
    elif isinstance(value, Color):
        return value
    else:
        raise ValidationException()

def _parse_transparent_color(value, render_device):
    if isinstance(value, Ident) and value == 'transparent':
        return value
    else:
        return _parse_color(value, render_device)

def _parse_border_shortcut(count):
    def f(value, render_device):
        width = 2
        style = Ident('none')
        color = None
        for v in value:
            if isinstance(v, Dimension):
                width = _parse_border_width(v, render_device)
            elif v in ['none', 'hidden', 'dotted', 'dashed', 'solid',
                       'double', 'groove', 'ridge', 'inset', 'outset']:
                style = _parse_border_style(v, render_device)
            else:
                color = _parse_transparent_color(v, render_device)

        return [width, style, color] * count
    return f

def _parse_border_width(value, render_device):
    if isinstance(value, Ident):
        if value == 'thin':
            return Dimension('1px')
        elif value == 'medium':
            return Dimension('2px')
        elif value == 'thick':
            return Dimension('4px')
        else:
            raise ValidationException()
    elif isinstance(value, Dimension):
        return value
    elif value == 0:
        return 0
    else:
        raise ValidationException()

def _parse_font_family(value, render_device):
    # Remove commas from list
    for v in value[1::2]:
        if v != ',':
            raise ValidationException()
    return value[::2]

_parse_margin = _parse_generic(Dimension, Percentage, 'auto', 0)
_parse_padding = _parse_generic(Dimension, Percentage, 'auto', 0)
_parse_line_height = _parse_generic(Number, Dimension, Percentage, 'normal')
_parse_font_size = _parse_generic(Dimension, Number, Percentage,
    'xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large')

_parse_vertical_align = _parse_generic(
    Percentage, Dimension, 
    'baseline', 'sub', 'super', 'top', 'text-top', 'middle', 'bottom',
    'text-bottom')
    
_parse_border_style = _parse_generic(
    'none', 'hidden', 'dotted', 'dashed', 'solid', 'double', 'groove',
    'ridge', 'inset', 'outset') 

_properties = {
#    CSS name,              Box attr,        
#       inhrtble, multivalue, parse function
    'background-color':     ('background_color',    
        True,   False,  _parse_transparent_color),
    'border':               (
        ['border_top_width', 'border_top_style', 'border_top_color',
         'border_right_width', 'border_right_style', 'border_right_color',
         'border_bottom_width', 'border_bottom_style', 'border_bottom_color',
         'border_left_width', 'border_left_style', 'border_left_color'],
        True,   True,   _parse_border_shortcut(4)),
    'border-top':           (
        ['border_top_width', 'border_top_style', 'border_top_color'],
        True,   True,   _parse_border_shortcut(1)),
    'border-right':           (
        ['border_right_width', 'border_right_style', 'border_right_color'],
        True,   True,   _parse_border_shortcut(1)),
    'border-bottom':           (
        ['border_bottom_width', 'border_bottom_style', 'border_bottom_color'],
        True,   True,   _parse_border_shortcut(1)),
    'border-left':           (
        ['border_left_width', 'border_left_style', 'border_left_color'],
        True,   True,   _parse_border_shortcut(1)),
    'border-color':         (
        ['border_top_color', 'border_right_color', 'border_bottom_color',
         'border_left_color'],
        True,   True,   _parse_shortcut(_parse_transparent_color)),
    'border-top-color':     ('border_top_color',
        True,   False,  _parse_transparent_color),
    'border-right-color':   ('border_right_color',
        True,   False,  _parse_transparent_color),
    'border-bottom-color':  ('border_bottom_color',
        True,   False,  _parse_transparent_color),
    'border-left-color':    ('border_left_color',
        True,   False,  _parse_transparent_color),
    'border-style':         (
        ['border_top_style', 'border_right_style', 'border_bottom_style',
         'border_left_style'],
        True,   True,   _parse_shortcut(_parse_border_style)),
    'border-top-style':     ('border_top_style',    
        True,   False,  _parse_border_style),
    'border-right-style':   ('border_right_style',  
        True,   False,  _parse_border_style),
    'border-bottom-style':  ('border_bottom_style', 
        True,   False,  _parse_border_style),
    'border-left-style':    ('border_left_style',   
        True,   False,  _parse_border_style),
    'border-width':         (
        ['border_top_width', 'border_right_width', 'border_bottom_width',
         'border_left_width'],
        True,   True,   _parse_shortcut(_parse_border_width)),
    'border-top-width':     ('border_top_width',    
        True,   False,  _parse_border_width),
    'border-right-width':   ('border_right_width',  
        True,   False,  _parse_border_width),
    'border-bottom-width':  ('border_bottom_width', 
        True,   False,  _parse_border_width),
    'border-left-width':    ('border_left_width',   
        True,   False,  _parse_border_width),
    'color':                ('color',               
        True,   False,  _parse_color),
    'display':              ('display',             
        True,   False,  _parse_generic(
            'inline', 'block', 'list-item', 'run-in', 'inline-block',
            'table', 'inline-table', 'table-row-group', 'table-header-group',
            'table-footer-group', 'table-row', 'table-column-group',
            'table-cell', 'table-caption', 'none')),
    'font-family':          ('font_family',         
        True,   True,   _parse_font_family),
    'font-size':            ('font_size',           
        True,   False,  _parse_font_size),
    'font-style':           ('font_style',
        True,   False,  _parse_generic('normal', 'italic', 'oblique')),
    'font-weight':          ('font_weight',
        True,   False,  _parse_generic(Number, 
            'normal', 'bold', 'bolder', 'lighter')),
    'height':               ('height',
        True,   False,  _parse_generic(Dimension, Percentage, 0, 'auto')),
    'line-height':          ('line_height',
        True,   False,  _parse_line_height),
    'margin':               (
        ['margin_top', 'margin_right', 'margin_bottom', 'margin_left'],
        True,   True,   _parse_shortcut(_parse_margin)),
    'margin-top':           ('margin_top',          
        True,   False,  _parse_margin),
    'margin-right':         ('margin_right',
        True,   False,  _parse_margin),
    'margin-bottom':        ('margin_bottom',
        True,   False,  _parse_margin),
    'margin-left':          ('margin_left',
        True,   False,  _parse_margin),
    'max-height':           ('max_height',
        True,   False,  _parse_generic(Dimension, Percentage, 0, 'none')),
    'max-width':            ('max_width',
        True,   False,  _parse_generic(Dimension, Percentage, 0, 'none')),
    'min-height':            ('min_height',
        True,   False,  _parse_generic(Dimension, Percentage, 0)),
    'min-width':            ('min_width',
        True,   False,  _parse_generic(Dimension, Percentage, 0)),
    'padding':              (
        ['padding_top', 'padding_right', 'padding_bottom', 'padding_left'],
        True,   True,   _parse_shortcut(_parse_padding)),
    'padding-top':          ('padding_top',
        True,   False,  _parse_padding),
    'padding-right':        ('padding_right',
        True,   False,  _parse_padding),
    'padding-bottom':       ('padding_bottom',
        True,   False,  _parse_padding),
    'padding-left':         ('padding_left',
        True,   False,  _parse_padding),
    'position':             ('position',            
        True,   False,  _parse_generic(
            'static', 'relative', 'absolute', 'fixed')),
    'vertical-align':       ('vertical_align',
        True,   False,  _parse_vertical_align),
    'width':                ('width',
        True,   False,  _parse_generic(Dimension, Percentage, 0, 'auto'))
}

def apply_style_declarations(declarations, box, render_device):
    for declaration in declarations:
        if declaration.property in _properties:
            attr, inheritable, multivalue, parse_func = \
                _properties[declaration.property]
            if not multivalue:
                if len(declaration.values) != 1:
                    continue
                value = declaration.values[0]
            else:
                value = declaration.values

            if (inheritable and 
                isinstance(value, Ident) and
                value == 'inherit' and
                box.parent):
                if type(attr) in (list, tuple):
                    for a in attr:
                        setattr(box, a, getattr(box.parent, a))
                else:
                    setattr(box, attr, getattr(box.parent, attr))
            else:
                try:
                    value = parse_func(value, render_device)
                    if type(attr) in (list, tuple):
                        for a, v in zip(attr, value):
                            setattr(box, a, v)
                    else:
                        setattr(box, attr, value)
                except ValidationException:
                    warnings.warn(
                        'CSS validation error in %s' % declaration.property)

# Properties that are inherited by default, as listed in Appendix F (visual,
# non-page only).
_inherited_properties = [
    'border_collapse',
    'border_spacing',
    'caption_side',
    'color',
    'cursor',
    'direction',
    'empty_cells',
    'font_family',
    'font_size',
    'font_style',
    'font_variant',
    'font_weight',
    'letter_spacing',
    'line_height',
    'list_style_image',
    'list_style_position',
    'list_style_type',
    'quotes',
    'text_align',
    'text_indent',
    'text_transform',
    'visibility',
    'white_space',
    'word_spacing',
]


def apply_inherited_style(box):
    if not box.parent:
        return
    d = box.parent.__dict__
    for attr in _inherited_properties:
        if attr in d:
            setattr(box, attr, d[attr])

def apply_style_string(style, box, render_device):
    scanner = Scanner(lexicon, StringIO(style))
    parser = Parser(scanner)
    declarations = parser.declaration_list()
    apply_style_declarations(declarations, box, render_device)

def apply_stylesheet(stylesheet, elem, box, render_device):
    declarations = stylesheet.get_declarations(elem)
    apply_style_declarations(declarations, box, render_device)
