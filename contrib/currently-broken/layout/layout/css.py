#!/usr/bin/env python

'''CSS 2.1 parsing and rule matching.

This module is distinct from the CSS 2.1 properties, which are contained
in properties.py; allowing users to use the CSS syntax and rule matching for
custom properties and applications if desired.

The Stylesheet class is the top-level interface to rules and declarations.
It contains methods for quickly retrieving matching declarations for a given
element.

Implement the SelectableElement interface on your objects to allow rule
matching based on attributes, ancestors and siblings.

Currently several features of CSS are unimplemented, such as media
declarations and the stylesheet priority in the cascade (this can be faked
by applying stylesheets in increasing order of priority, with only !important
declarations being sorted incorrectly).
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from StringIO import StringIO
import warnings

from Plex import *
from Plex.Traditional import re

from layout.base import *

# Interfaces
# ---------------------------------------------------------------------------

class SelectableElement(object):
    '''Elements must implement this interface to allow CSS selectors to
    traverse them.
    '''
    parent = None               # SelectableElement
    previous_sibling = None     # SelectableElement
    attributes = None           # dict of str: str
    id = None                   # str
    classes = ()                # list of str
    name = None                 # str
    pseudo_classes = ()         # set of str (without colon)

    def add_pseudo_class(self, c):
        if self.pseudo_classes == ():
            self.pseudo_classes = set()
        self.pseudo_classes.add(c)

    def remove_pseudo_class(self, c):
        if self.pseudo_classes is not None:
            self.pseudo_classes.remove(c)

    # Debug methods only
    def short_repr(self):
        s = self.name
        if self.id:
            s += '#%s' % self.id
        for c in self.classes:
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

# Stylesheet objects
# ---------------------------------------------------------------------------
class RuleSet(object):
    '''Primary set is a collection of rules, organised for quick matching
    against an element.
    '''
    def __init__(self):
        self.names = {}
        self.ids = {}
        self.classes = {}
        self.universals = []

    def add_rule(self, rule):
        primary = rule.selector.primary
        if primary.name:
            self.add_name(primary.name, rule)
        elif primary.id:
            self.add_id(primary.id, rule)
        elif primary.classes:
            self.add_classes(primary.classes, rule)
        else:
            self.add_universal(rule)
                
    def add_name(self, name, rule):
        if name not in self.names:
            self.names[name] = []
        self.names[name].append(rule)

    def add_id(self, id, rule):
        if id not in self.ids:
            self.ids[id] = []
        self.ids[id].append(rule)

    def add_classes(self, classes, rule):
        for klass in classes:
            if klass not in self.classes:
                self.classes[klass] = []
            self.classes[klass].append(rule)

    def add_universal(self, rule):
        self.universals.append(rule)

    def get_matching_rules(self, elem):
        '''Return a list of declarations that should be applied to the
        given element.

        The element must implement the SelectableElement interface.  The
        declarations are returned in the order that they should be applied
        (sorted in increasing specifity).  Redundant declarations are
        currently not filtered out.
        '''
        # Quickly get some starting points.
        primaries = []
        primaries += self.names.get(elem.name, [])
        if elem.id:
            primaries += self.ids.get(elem.id, [])
        for c in elem.classes or ():
            primaries += self.classes.get(c, [])
        primaries += self.universals

        # Filter out non-matching
        matches = [rule for rule in primaries if self.matches(rule, elem)]

        # Order by specifity
        matches.sort(lambda a,b: a.specifity - b.specifity)

        return matches

    def matches(self, rule, elem):
        '''Determine if the given rule applies to the given element.  Returns
        True if so, False otherwise.

        # XXX why isn't this on Rule?
        '''
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

class Stylesheet(object):
    '''Top-level container for rules and declarations.  Typically initialised
    from a CSS stylesheet file.  Elements can then be searched for matching
    declarations.
    '''

    def __init__(self, data):
        '''Initialise the stylesheet with the given data, which can be
        a string or file-like object.

        Most parse errors are ignored as defined in the CSS specification.
        Any that slip through as exceptions are bugs.
        '''
        if not hasattr(data, 'read'):
            data = StringIO(data)
        scanner = Scanner(lexicon, data)
        parser = Parser(scanner)
        charset, imports, rules = parser.stylesheet()

        self.rules = rules      # only for debugging

        self.ruleset = RuleSet()
        for rule in rules:
            self.ruleset.add_rule(rule)

    def get_element_declaration_sets(self, element):
        return [rule.declaration_set for rule in self.ruleset.get_matching_rules(element)]

    def get_declarations(self, element):
        # XXX deprecated
        declarations = []
        for declaration_set in self.get_element_declaration_sets(element):
            declarations += declaration_set.declarations
        return declarations

    def matches(self, rule, elem):
        return self.ruleset.matches(rule, elem)

    def pprint(self):
        for rule in self.rules:
            rule.pprint()

def parse_style_declaration_set(style):
    scanner = Scanner(lexicon, StringIO(style))
    parser = Parser(scanner)
    declaration_set = parser.declaration_set()
    return declaration_set

def parse_style_expression(value):
    scanner = Scanner(lexicon, StringIO(value))
    parser = Parser(scanner)
    return parser.expr()
    

class Import(object):
    '''An @import declaration.  Currently ignored.
    '''
    def __init__(self, location, media):
        self.location = location
        self.media = media

    def pprint(self):
        print '@import', self.location, ','.join(self.media)

class Page(object):
    '''An @page declaration.  Currently ignored.
    '''
    def __init__(self, pseudo, declaration_set):
        self.pseudo = pseudo
        self.declaration_set = declaration_set

class Rule(object):
    '''A rule, consisting of a single selector and one or more declarations.
    The rule may also contain one or more media strings, but these are
    currently ignored.
    '''
    media = None

    def __init__(self, selector, declaration_set):
        self.selector = selector
        self.declaration_set = declaration_set

        # Specifity calculated according to 6.4.3 with base 256
        specifity = 0
        simples = [selector.primary] + [s.simple for s in selector.combiners]
        for s in simples:
            if s.id:
                specifity += 1 << 16
            specifity += (1 << 8) * (len(s.classes) + 
                                     len(s.attribs) + 
                                     len(s.pseudos))
            if s.name:
                specifity += 1
        self.specifity = specifity

    def is_media(self, media):
        '''Return True if this rule applies to the given media string.'''
        return (self.media is None or
                'all' in self.media or 
                media in self.media)

    def pprint(self):
        if self.media:
            print '@media', ','.join(self.media), '{', 
        self.selector.pprint()
        print '{'
        self.declaration_set.pprint()
        print '}'

class Selector(object):
    '''A single selector, consisting of a primary SimpleSelector and zero or
    more combining selectors.  
    
    The primary selector is the final selector in a sequence of descendent and
    sibling operators, and is the starting point for searches.  The combiners
    list is "backwards", running from closest descendent/sibling to most
    distant (opposite order to that listed in the CSS file.
    '''
    def __init__(self, primary, combiners):
        self.primary = primary
        self.combiners = combiners

    @staticmethod
    def from_string(data):
        scanner = Scanner(lexicon, StringIO(data.strip()))
        parser = Parser(scanner)
        return parser.selector()

    def pprint(self):
        print 'Selector(primary=%r,combiners=%r)' % \
            (self.primary, self.combiners),

class SimpleSelector(object):
    '''A single selector consisting of an optional name, id, class list,
    attribute value list and pseudo-class/element appliers.  If none of these
    are present, the selector is a universal selector.
    '''
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
        '''Determines if the selector matches the given element.  Returns True
        if so, False otherwise.
        '''
        if self.name is not None and elem.name != self.name:
            return False
        if self.id is not None and elem.id != self.id:
            return False
        for c in self.classes:
            if c not in elem.classes:
                return False
        for attr in self.attribs:
            if not elem.attributes.has_key(attr):
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
        for pseudo in self.pseudos:
            if pseudo.name not in elem.pseudo_classes:
                return False
        return True
        
class CombiningSelector(object):
    '''A selector and the combinator required to reach the element this selector
    should be applied to.  
     
    The combinator can be one of '' (ancestor), '>' (parent) or '+' (previous
    sibling).
    '''

    def __init__(self, combinator, simple):
        self.combinator = combinator
        self.simple = simple

    def __repr__(self):
        return '%s%r' % (self.combinator or '', self.simple)

class Attrib(object):
    '''An attribute name, and optional value and comparison operator.  
    
    If no operator is given, the attribute is merely checked for existence.
    The operator can be one of '=', '|=', '~='.  Values must be strings.
    '''
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
    '''A pseudo-class or pseudo-element declaration.
    
    The 'name' value does not include the ':' symbol.
    '''
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return ':%s' % self.name

class PseudoFunction(Pseudo):
    '''A function applied as a pseudo-element or pseudo-class.  Currently
    unused.
    '''
    def __init__(self, name, param):
        super(PseudoFunction, self).__init__(name)
        self.param = param

    def __repr__(self):
        return ':%s(%s)' % (self.name, self.param)

class DeclarationSet(object):
    '''Set of declarations, for example within a rule block.
    '''
    def __init__(self, declarations):
        self.declarations = declarations

    def __str__(self):
        return '; '.join([str(d) for d in self.declarations])

    def pprint(self):
        for declaration in self.declarations:
            print declaration, ';'

class Declaration(object):
    '''A single declaration, consisting of a property name, a list of values,
    and optional priority.

    The property name must be a string, the list of values is typically one in
    length, but may have several values (for example, a shortcut property).
    If the property has several values separated by commas, these commas
    appear as separate items in the value list.  If specified, the priority is
    the string '!important', otherwise empty.
    '''
    def __init__(self, property, values, priority):
        self.property = property
        self.values = values
        self.priority = priority

    def __str__(self):
        s = '%s: %s' % (self.property, ' '.join([str(v) for v in self.values]))
        if self.priority:
            s += ' ! important'
        return s

    def __repr__(self):
        s = '%s: %r' % (self.property, self.values)
        if self.priority:
            s += ' ! important'
        return '%s(%s)' % (self.__class__.__name__, s)

# Scanner tokens (in addition to the basic types given in base.py)
# ----------------------------------------------------------------
class Hash(str):
    '''A keyword beginning with a hash, or a colour hash.   Value does not
    include the '#" symbol.'''
    def __new__(cls, text):
        return str.__new__(cls, text[1:])

class AtKeyword(str):
    '''An keyword such as @media, @import, etc.  Includes the '@' symbol.'''
    def __new__(cls, text):
        return str.__new__(cls, text.lower())

class CDO(object):
    '''Comment delimiter open token '<!--'.'''
    pass

class CDC(object):
    '''Comment delimiter close token '-->'.'''
    pass

class Whitespace(object):
    pass

class Function(str):
    '''A function name, including the '(' at the end signifying the beginning
    of a function call.
    '''
    pass

class Important(object):
    '''The '!important' token.'''
    pass

class Delim(str):
    '''Any other punctuation, such as comma, period, operator.'''
    pass

# Scanner macros
# ----------------------------------------------------------------------------

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

# Scanner tokens
# ----------------------------------------------------------------------------

IDENT = ident
ATKEYWORD = Str('@') + ident
STRING = string
HASH = Str('#') + name
NUMBER = num
PERCENTAGE = num + Str('%')
DIMENSION = num + ident
URITOKEN = (NoCase(Str('url(')) + w + string + w + Str(')')) | \
           (NoCase(Str('url(')) + w + 
            # XXX Following is in CSS spec (twice!) but clearly wrong
            #Rep(Any('!#$%&*-~')|nonascii|escape) + w + Str(')'))
            # Using this instead:
            Rep(AnyBut(')')) + w + Str(')'))
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
    (URITOKEN, lambda s,t: URI(t)),
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

# Parser
# ----------------------------------------------------------------------------

class ParserException(Exception):
    def __init__(self,  file, line, col):
        self.file = file
        self.line = line
        self.col = col

    def __str__(self):
        return 'Parse error in "%s" at line %d, column %d' % \
            (self.file, self.line, self.col)

class UnexpectedToken(ParserException):
    def __init__(self, position, expected_list, got_token):
        ParserException.__init__(self, *position)
        if len(expected_list) == 1:
            self.expected = 'expected %r' % expected_list[0]
        else:
            self.expected = 'expected one of %r' % expected_list
        self.expected_list = expected_list
        self.got_token = got_token

    def __str__(self):
        return '%s: %s, got %r' % \
            (super(UnexpectedToken, self).__str__(), 
             self.expected, self.got_token)

class Parser(object):
    '''Grammar parser for CSS 2.1.

    This is a hand-coded LL(1) parser.  There are convenience functions for
    peeking at the next token and checking if the next token is of a given type
    or delimiter.  Otherwise, it is a straightforward recursive implementation
    of the production rules given in Appendix G.1.

    Some attention is paid to ignoring errors according to the specification,
    but this is not perfect yet.  In particular, some parse errors will result
    in an exception, which halts parsing.
    '''

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
            raise UnexpectedToken(self._scanner.position(), _types, r)
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
        declaration_set = self.declaration_set()
        self._read('}')
        self._eat_whitespace()
        return Page(pseudo, declaration_set)

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
        declaration_set = self.declaration_set()
        self._read('}')
        self._eat_whitespace()

        return [Rule(s, declaration_set) for s in selectors]

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

    def declaration_set(self):
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
        return DeclarationSet(declarations)

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

