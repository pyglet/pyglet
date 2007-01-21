#!/usr/bin/env python

'''Parse a C source file.

Unlike the ctypes-gen wrapper or GCC-XML, preprocessing is done in the same
pass as parsing, and are included in the grammar.  Macros are expanded as
usual (but not macro functions).

The lexicon is complete, however the grammar is only currently equipped for
declarations (function implementations will cause a parse error).  Structs, 
enums, and initializer values are also not handled yet and will cause a parse
error.

Preprocessing behaviour is not like an ordinary compiler:

  * Preprocessor declarations can occur only between declarations (i.e., not
    in the middle of one).  
  * Macros are expanded as usual (except for function macros).
  * #define and #undef behave as usual.
  * #ifdef, #ifndef, #if and #else are ignored, with the exception of 
    #ifdef __cplusplus, whose contents are skipped.  (This handling should be
    improved TODO).

To use, subclass CParser and override its handle_* methods.  Then instantiate
the class with a string to parse.

Derived from ANSI C grammar:
  * Lexicon: http://www.lysator.liu.se/c/ANSI-C-grammar-l.html
  * Grammar: http://www.lysator.liu.se/c/ANSI-C-grammar-y.html

Reference is C99:
  * http://www.open-std.org/JTC1/SC22/WG14/www/docs/n1124.pdf

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import re
import sys

# lex and yacc are from PLY (http://www.dabeaz.com/ply) but have been modified
# for this tool.  See README in this directory.
import lex
import yacc

__all__ = ['CParser', 'DebugCParser',
           'Declaration', 'Pointer', 'Declarator', 'Array', 'Parameter',
           'Type']

states = (
    ('skip', 'exclusive'),
    ('pp', 'exclusive'),
)

tokens = (
    'PREPROCESSOR_DEFINE', 'PREPROCESSOR_UNDEF', 'PREPROCESSOR_IF',
    'PREPROCESSOR_IFDEF', 'PREPROCESSOR_IFNDEF', 'PREPROCESSOR_ENDIF',
    'PREPROCESSOR_UNKNOWN', 'PREPROCESSOR_NEWLINE',

    'IDENTIFIER', 'CONSTANT', 'STRING_LITERAL', 'SIZEOF',

    'PTR_OP', 'INC_OP', 'DEC_OP', 'LEFT_OP', 'RIGHT_OP', 'LE_OP', 'GE_OP',
    'EQ_OP', 'NE_OP', 'AND_OP', 'OR_OP', 'MUL_ASSIGN', 'DIV_ASSIGN',
    'MOD_ASSIGN', 'ADD_ASSIGN', 'SUB_ASSIGN', 'LEFT_ASSIGN', 'RIGHT_ASSIGN',
    'AND_ASSIGN', 'XOR_ASSIGN', 'OR_ASSIGN', 'TYPE_NAME', 
    
    'TYPEDEF', 'EXTERN', 'STATIC', 'AUTO', 'REGISTER', 
    'CHAR', 'SHORT', 'INT', 'LONG', 'SIGNED', 'UNSIGNED', 'FLOAT', 'DOUBLE',
    'CONST', 'VOLATILE', 'VOID',
    'STRUCT', 'UNION', 'ENUM', 'ELLIPSIS',

    'CASE', 'DEFAULT', 'IF', 'ELSE', 'SWITCH', 'WHILE', 'DO', 'FOR', 'GOTO',
    'CONTINUE', 'BREAK', 'RETURN'
)

keywords = [
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
    'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'int',
    'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
    'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile',
    'while'
]

subs = {
    'D': '[0-9]',
    'L': '[a-zA-Z_]',
    'H': '[a-fA-F0-9]',
    'E': '[Ee][+-]?{D}+',
    'FS': '[FflL]',
    'IS': '[uUlL]*',
}

# Special handling of preprocessing: return a complete token for
# any line beginning with '#'
def t_preprocessor(t):
    r'(^\#|\n\#).*'
    # DOTALL is not given, so regex terminates at EOL

    # Trap the '\n' token when it comes.
    t.lexer.push_state('pp')

    # Parse the pp line now, so we can act on #define and #undef
    # within the lexer straight away.  The returned token is
    # used in the grammar to call the CParser handle_* methods at
    # the correct time.

    # Get rid of leading newline
    line = t.value
    if line[0] == '\n':
        t.lexer.lineno += 1
        line = line[1:]

    # Split into #cmd param
    s = line[1:].strip().split(None, 1)
    if len(s) > 1:
        cmd, param = s
    else:
        cmd, param = s[0], ''

    # Return correct token for each cmd and also update lex defines
    if cmd == 'define':
        s = param.split(None, 1)
        if len(s) > 1:
            name, value = s
        else:
            name, value = s[0], ''
        if value in t.lexer.defines:
            value = t.lexer.defines[value]
        t.lexer.defines[name] = value
        t.type = 'PREPROCESSOR_DEFINE'
        t.value = (name, value)
    elif cmd == 'undef':
        del t.lexer.defines[param]
        t.type = 'PREPROCESSOR_UNDEF'
        t.value = param
    elif cmd == 'if':
        t.type = 'PREPROCESSOR_IF'
        t.value = param
    elif cmd == 'ifdef':
        t.type = 'PREPROCESSOR_IFDEF'
        t.value = param
    elif cmd == 'ifndef':
        t.type = 'PREPROCESSOR_IFNDEF'
        t.value = param
    elif cmd == 'endif':
        t.type = 'PREPROCESSOR_ENDIF'
    else:
        t.type = 'PREPROCESSOR_UNKNOWN'

    return t

t_skip_preprocessor = t_preprocessor

# Substitute {foo} with subs[foo] in string (makes regexes more lexy)
sub_pattern = re.compile('{([^}]*)}')
def sub_repl_match(m):
    return subs[m.groups()[0]]
def sub(s):
    return sub_pattern.sub(sub_repl_match, s)

TOKEN = lex.TOKEN
@TOKEN(sub('{L}({L}|{D})*'))
def t_check_type(t):
    if t.value in t.lexer.defines:
        # Messy: insert replacement text before lexpos, then move back
        # lexpos to read it.  len(replacement text) is always less than
        # lexpos, since its #define must have preceeded it.  This is not
        # true if #include processing is done (it is not currently, so
        # no problem).
        repl = t.lexer.defines[t.value]
        pos = t.lexer.lexpos
        t.lexer.lexdata = t.lexer.lexdata[:pos-len(repl)] + \
            repl + t.lexer.lexdata[pos:]
        t.lexer.lexpos -= len(repl)
        return None

    elif t.value in keywords:
        t.type = t.value.upper()
    elif t.value in t.lexer.type_names:
        t.type = 'TYPE_NAME'
    else:
        t.type = 'IDENTIFIER'
    return t

@TOKEN(sub('0[xX]{H}+{IS}?'))
def t_hex_literal(t):
    t.type = 'CONSTANT'
    return t

@TOKEN(sub('0{D}+{IS}?'))
def t_oct_literal(t):
    t.type = 'CONSTANT'
    return t

@TOKEN(sub('{D}+{IS}?'))
def t_dec_literal(t):
    t.type = 'CONSTANT'
    return t

@TOKEN(sub(r"L?'(\\.|[^\\'])+'"))
def t_char_literal(t):
    t.type = 'CONSTANT'
    return t

@TOKEN(sub('{D}+{E}{FS}?'))
def t_float_literal1(t):
    t.type = 'CONSTANT'
    return t

@TOKEN(sub(r'{D}*\\.{D}+({E})?{FS}?'))
def t_float_literal2(t):
    t.type = 'CONSTANT'
    return t

@TOKEN(sub(r'{D}+\\.{D}*({E})?{FS}?'))
def t_float_literal3(t):
    t.type = 'CONSTANT'
    return t

@TOKEN(sub(r'L?"(\\.|[^\\"])*"'))
def t_string_literal(t):
    t.type = 'STRING_LITERAL'
    return t

t_ELLIPSIS = r'\.\.\.'
t_RIGHT_ASSIGN = r'>>='
t_LEFT_ASSIGN = r'<<='
t_ADD_ASSIGN = r'\+='
t_SUB_ASSIGN = r'-='
t_MUL_ASSIGN = r'\*='
t_DIV_ASSIGN = r'/='
t_MOD_ASSIGN = r'%='
t_AND_ASSIGN = r'&='
t_XOR_ASSIGN = r'\^='
t_OR_ASSIGN = r'\|='
t_RIGHT_OP = r'>>'
t_LEFT_OP = r'<<'
t_INC_OP = r'\+\+'
t_DEC_OP = r'--'
t_PTR_OP = r'->'
t_AND_OP = r'&&'
t_OR_OP = r'\|\|'
t_LE_OP = r'<='
t_GE_OP = r'>='
t_EQ_OP = r'=='
t_NE_OP = r'!='

# Doesn't handle archaic literals such as <%, %>, etc.
literals = ';{},:=()[].&!~-+*/%<>^|?'

# C /* comments */.  Copied from the ylex.py example in PLY: it's not 100%
# correct for ANSI C, but close enough for anything that's not crazy.
def t_ccomment(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

def t_INITIAL_skip_newline(t):
    r'\n'
    # Only match one newline, otherwise preprocessing is screwed up.
    t.lexer.lineno += 1

def t_pp_newline(t):
    r'\n'
    t.type = 'PREPROCESSOR_NEWLINE'
    t.lexer.pop_state()
    # After the newline is returned, we need to scan it again in INITIAL
    # state so that another preprocessor line can be parsed if necessary.
    t.lexer.lexpos -= 1
    return t

def t_skip_any(t):
    r'[^\n\#]+'

t_ignore = ' \t\v\f'
t_skip_ignore = ' \t\v\f'
t_pp_ignore = ''

def t_error(t):
    t.lexer.skip(1)

t_skip_error = t_pp_error = t_error

lex.lex()

# Returned grammar objects: these make up the object model.
class Declaration(object):
    def __init__(self):
        self.declarator = None
        self.type = Type()
        self.storage = None

    def __repr__(self):
        d = {
            'declarator': self.declarator,
            'type': self.type,
        }
        if self.storage:
            d['storage'] = self.storage
        l = ['%s=%r' % (k, v) for k, v in d.items()]
        return 'Declaration(%s)' % ', '.join(l)

class Declarator(object):
    pointer = None
    def __init__(self):
        self.identifier = None
        self.initializer = None
        self.array = None
        self.parameters = None

    def __repr__(self):
        s = self.identifier or ''
        if self.array:
            s += repr(self.array)
        if self.initializer:
            s += ' = %r' % self.initializer
        if self.parameters is not None:
            s += '(' + ', '.join([repr(p) for p in self.parameters]) + ')'
        return s

abstract_declarator = Declarator()

class Pointer(Declarator):
    pointer = None
    def __init__(self):
        super(Pointer, self).__init__()
        self.qualifiers = []

    def __repr__(self):
        q = ''
        if self.qualifiers:
            q = '<%s>' % ' '.join(self.qualifiers)
        return 'POINTER%s(%r)' % (q, self.pointer) + \
            super(Pointer, self).__repr__()

class Array(object):
    def __init__(self):
        self.size = None
        self.array = None

    def __repr__(self):
        if self.size:
            a =  '[%r]' % self.size
        else:
            a = '[]'
        if self.array:
            return repr(self.array) + a
        else:
            return a

class Parameter(object):
    def __init__(self):
        self.type = Type()
        self.storage = None
        self.declarator = None

    def __repr__(self):
        d = {
            'type': self.type,
        }
        if self.declarator:
            d['declarator'] = self.declarator
        if self.storage:
            d['storage'] = self.storage
        l = ['%s=%r' % (k, v) for k, v in d.items()]
        return 'Parameter(%s)' % ', '.join(l)


class Type(object):
    def __init__(self):
        self.qualifiers = []
        self.specifiers = []

    def __repr__(self):
        return ' '.join(self.qualifiers + self.specifiers)

# These are used only internally.

class StorageClassSpecifier(str):
    pass

class TypeSpecifier(str):
    pass

class TypeQualifier(str):
    pass

def apply_specifiers(specifiers, declaration):
    '''Apply specifiers to the declaration (declaration may be
    a Parameter instead).'''
    for s in specifiers:
        if type(s) == StorageClassSpecifier:
            if declaration.storage:
                p.parser.cparser.handle_error(
                    'Declaration has more than one storage class', 
                    p.lineno(1))
                return
            declaration.storage = s
        elif type(s) == TypeSpecifier:
            declaration.type.specifiers.append(s)
        elif type(s) == TypeQualifier:
            declaration.type.qualifiers.append(s)

# Grammar production rules (the parse table is built by PLY using reflection
# on the docstrings).
def p_translation_unit(p):
    '''translation_unit : external_declaration
                        | translation_unit external_declaration
    '''
    # Starting production.
    # Intentionally empty

def p_external_declaration(p):
    '''external_declaration : declaration ';'
                            | preprocessor PREPROCESSOR_NEWLINE
    '''
    # The ';' must be here, not in 'declaration', as declaration needs to
    # be executed before the ';' is shifted (otherwise the next lookahead will
    # be read, which may be affected by this declaration if its a typedef.

    # Not handled: function_definition
    # Special: preprocessor 
    # Intentionally empty

def p_constant_expression(p):
    '''constant_expression : conditional_expression
    '''
    p[0] = p[1]

def p_conditional_expression(p):
    '''conditional_expression : CONSTANT
                              | IDENTIFIER
    '''
    # Not handled: ternary operator, logical_or_expression
    p[0] = p[1]

def p_declaration(p):
    '''declaration : declaration_specifiers
                   | declaration_specifiers init_declarator_list
    '''
    declaration = Declaration()
    apply_specifiers(p[1], declaration)

    if len(p) == 2:
        p.parser.cparser.impl_handle_declaration(declaration)
        return

    for declarator in p[2]:
        declaration.declarator = declarator
        p.parser.cparser.impl_handle_declaration(declaration)

def p_declaration_error(p):
    '''declaration : error ';'
    '''
    # Error resynchronisation catch-all

def p_declaration_specifiers(p):
    '''declaration_specifiers : storage_class_specifier
                              | storage_class_specifier declaration_specifiers
                              | type_specifier
                              | type_specifier declaration_specifiers
                              | type_qualifier
                              | type_qualifier declaration_specifiers
    '''
    if len(p) > 2:
        p[0] = (p[1],) + p[2]
    else:
        p[0] = (p[1],)

def p_init_declarator_list(p):
    '''init_declarator_list : init_declarator
                            | init_declarator_list ',' init_declarator
    '''
    if len(p) > 2:
        p[0] = p[1] + (p[3],)
    else:
        p[0] = (p[1],)

def p_init_declarator(p):
    '''init_declarator : declarator
                       | declarator '=' initializer
    '''
    p[0] = p[1]
    if len(p) > 2:
        p[0].initializer = p[2]

def p_storage_class_specifier(p):
    '''storage_class_specifier : TYPEDEF
                               | EXTERN
                               | STATIC
                               | AUTO
                               | REGISTER
    '''
    p[0] = StorageClassSpecifier(p[1])

def p_type_specifier(p):
    '''type_specifier : VOID
                      | CHAR
                      | SHORT
                      | INT
                      | LONG
                      | FLOAT
                      | DOUBLE
                      | SIGNED
                      | UNSIGNED
                      | TYPE_NAME
    '''
    # Not handled: struct_or_union_specifier, enum_specifier
    p[0] = TypeSpecifier(p[1])

def p_type_qualifier(p):
    '''type_qualifier : CONST
                      | VOLATILE
    '''
    p[0] = TypeQualifier(p[1])

def p_declarator(p):
    '''declarator : pointer direct_declarator
                  | direct_declarator
    '''
    if len(p) > 2:
        p[0] = p[1]
        ptr = p[1]
        while ptr.pointer:
            ptr = ptr.pointer
        ptr.pointer = p[2]
    else:
        p[0] = p[1]

def p_direct_declarator(p):
    '''direct_declarator : IDENTIFIER
                         | '(' declarator ')'
                         | direct_declarator '[' constant_expression ']'
                         | direct_declarator '[' ']'
                         | direct_declarator '(' parameter_type_list ')'
                         | direct_declarator '(' identifier_list ')'
                         | direct_declarator '(' ')'
    '''
    if isinstance(p[1], Declarator):
        p[0] = p[1] 
        if p[2] == '[':
            a = Array()
            a.array = p[0].array
            p[0].array = a
            if p[3] != ']':
                a.size = p[3]
        else:
            if p[3] == ')':
                p[0].parameters = ()
            else:
                p[0].parameters = p[3]
    elif p[1] == '(':
        p[0] = p[2]
    else:
        p[0] = Declarator()
        p[0].identifier = p[1]

    # Check parameters for (void) and simplify to empty tuple.
    if p[0].parameters and len(p[0].parameters) == 1:
        param = p[0].parameters[0]
        if param.type.specifiers == ['void'] and not param.declarator:
            p[0].parameters = ()


def p_pointer(p):
    '''pointer : '*'
               | '*' type_qualifier_list
               | '*' pointer
               | '*' type_qualifier_list pointer
    '''
    if len(p) == 2:
        p[0] = Pointer()
    elif len(p) == 3:
        if type(p[2]) == Pointer:
            p[0] = Pointer()
            p[0].pointer = p[2]
        else:
            p[0] = Pointer()
            p[0].qualifiers = p[2]
    else:
        p[0] = Pointer()
        p[0].qualifiers = p[2]
        p[0].pointer = p[3]

def p_type_qualifier_list(p):
    '''type_qualifier_list : type_qualifier
                           | type_qualifier_list type_qualifier
    '''
    if len(p) > 2:
        p[0] = p[1] + (p[2],)
    else:
        p[0] = (p[1],)

def p_parameter_type_list(p):
    '''parameter_type_list : parameter_list
                           | parameter_list ',' ELLIPSIS
    '''
    if len(p) > 2:
        p[0] = p[1] + (p[3],)
    else:
        p[0] = p[1]


def p_parameter_list(p):
    '''parameter_list : parameter_declaration
                      | parameter_list ',' parameter_declaration
    '''
    if len(p) > 2:
        p[0] = p[1] + (p[3],)
    else:
        p[0] = (p[1],)

def p_parameter_declaration(p):
    '''parameter_declaration : declaration_specifiers declarator
                             | declaration_specifiers abstract_declarator
                             | declaration_specifiers
    '''
    p[0] = Parameter()
    apply_specifiers(p[1], p[0])
    if len(p) > 2:
        p[0].declarator = p[2]


def p_identifier_list(p):
    '''identifier_list : IDENTIFIER
                       | identifier_list ',' IDENTIFIER
    '''
    param = Parameter()
    param.declarator = Declarator()
    if len(p) > 2:
        param.declarator.identifier = p[3]
        p[0] = p[1] + (param,)
    else:
        param.declarator.identifier = p[1]
        p[0] = (param,)

def p_abstract_declarator(p):
    '''abstract_declarator : pointer
                           | direct_abstract_declarator
                           | pointer direct_abstract_declarator
    '''
    if len(p) == 2:
        p[0] = p[1]
        if type(p[0]) == Pointer:
            ptr = p[0]
            while ptr.pointer:
                ptr = ptr.pointer
            ptr.pointer = abstract_declarator
    else:
        p[0] = p[1]
        ptr = p[0]
        while ptr.pointer:
            ptr = ptr.pointer
        ptr.pointer = p[2]

def p_direct_abstract_declarator(p):
    '''direct_abstract_declarator : '(' abstract_declarator ')'
                      | '[' ']'
                      | '[' constant_expression ']'
                      | direct_abstract_declarator '[' ']'
                      | direct_abstract_declarator '[' constant_expression ']'
                      | '(' ')'
                      | '(' parameter_type_list ')'
                      | direct_abstract_declarator '(' ')'
                      | direct_abstract_declarator '(' parameter_type_list ')'
    '''
    if p[1] == '(' and isinstance(p[2], Declarator):
        p[0] = p[2]
    else:
        if isinstance(p[1], Declarator):
            p[0] = p[1]
            if p[2] == '[':
                a = Array()
                a.array = p[0].array
                p[0].array = a
                if p[3] != ']':
                    p[0].array.size = p[3]
            elif p[2] == '(':
                if p[3] == ')':
                    p[0].parameters = ()
                else:
                    p[0].parameters = p[3]
        else:
            p[0] = Declarator()
            if p[1] == '[':
                p[0].array = Array()
                if p[2] != ']':
                    p[0].array.size = p[2]
            elif p[1] == '(':
                if p[2] == ')':
                    p[0].parameters = ()
                else:
                    p[0].parameters = p[2]

def p_initializer(p):
    '''initializer : assignment_expression
                   | '{' initializer_list '}'
                   | '{' initializer_list ',' '}'
    '''

def p_initializer_list(p):
    '''initializer_list : initializer
                        | initializer_list ',' initializer
    '''

def p_assignment_expression(p):
    '''assignment_expression : IDENTIFIER
    '''
    # Not handled: anything. 

def p_preprocessor(p):
    '''preprocessor : preprocessor_define
                    | preprocessor_undef
                    | preprocessor_if
                    | preprocessor_ifdef
                    | preprocessor_ifndef
                    | preprocessor_endif
                    | PREPROCESSOR_UNKNOWN
    '''
    # Intentionally empty

def p_preprocessor_define(p):
    '''preprocessor_define : PREPROCESSOR_DEFINE'''
    p.parser.cparser.handle_define(p[1][0], p[1][1])

def p_preprocessor_undef(p):
    '''preprocessor_undef : PREPROCESSOR_UNDEF'''
    p.parser.cparser.handle_undef(p[1])

def p_preprocessor_if(p):
    '''preprocessor_if : PREPROCESSOR_IF'''
    p.parser.cparser.handle_if(p[1])

def p_preprocessor_ifdef(p):
    '''preprocessor_ifdef : PREPROCESSOR_IFDEF'''
    p.parser.cparser.handle_ifdef(p[1])

def p_preprocessor_ifndef(p):
    '''preprocessor_ifndef : PREPROCESSOR_IFNDEF'''
    p.parser.cparser.handle_ifndef(p[1])

def p_preprocessor_endif(p):
    '''preprocessor_endif : PREPROCESSOR_ENDIF'''
    p.parser.cparser.handle_endif()

def p_error(t):
    if not t:
        # Crap, no way to get to CParser instance.  FIXME TODO
        print >> sys.stderr, 'Syntax error at end of file.'
    else:
        t.lexer.cparser.handle_error('Syntax error at %r' % t.value, 
            t.lexer.lineno)
    # Don't alter lexer: default behaviour is to pass error production
    # up until it hits the catch-all at declaration, at which point
    # parsing continues (synchronisation).

class CParser(object):
    '''Parse a C source file.

    Subclass and override the handle_* methods.  Call `parse` with a string
    to parse.
    '''
    def __init__(self):
        self.lexer = lex.lex()
        self.lexer.defines = {}
        self.lexer.type_names = set()
        self.lexer.cparser = self

        self.parser = yacc.yacc() 
        self.parser.cparser = self
    
    def parse(self, data, debug=False):
        '''Parse a source string.

        If `debug` is True, parsing state is dumped to stdout.
        '''
        if not data.strip():
            return

        self.parser.parse(data, debug=debug)

    # Parser interface.  Override these methods in your subclass.

    def handle_error(self, message, lineno):
        '''A parse error occured.  
        
        The default implementation prints `lineno` and `message` to stderr.
        The parser will try to recover from errors by synchronising at the
        next semicolon.
        '''
        print >> sys.stderr, '%s:' % lineno, message

    def handle_define(self, name, value):
        '''#ifdef `name` `value` (both are strings)'''
        pass

    def handle_undef(self, name):
        '''#undef `name`'''
        pass

    def handle_if(self, expr):
        '''#if `expr`'''
        self.lexer.push_state(self.lexer.lexstate)

    def handle_ifdef(self, name):
        '''#ifdef `name`'''
        if name == '__cplusplus':
            self.lexer.push_state('skip')
        else:
            self.lexer.push_state(self.lexer.lexstate)

    def handle_ifndef(self, name):
        '''#ifndef `name`'''
        self.lexer.push_state(self.lexer.lexstate)

    def handle_endif(self):
        '''#endif'''
        self.lexer.pop_state()
        pass

    def impl_handle_declaration(self, declaration):
        '''Internal method that calls `handle_declaration`.  This method
        also adds any new type definitions to the lexer's list of valid type
        names, which affects the parsing of subsequent declarations.
        '''
        if declaration.storage == 'typedef':
            declarator = declaration.declarator
            while declarator.pointer:
                declarator = declarator.pointer
            self.lexer.type_names.add(declarator.identifier)
        self.handle_declaration(declaration)

    def handle_declaration(self, declaration):
        '''A declaration was encountered.  
        
        `declaration` is an instance of Declaration.  Where a declaration has
        multiple initialisers, each is returned as a separate declaration.
        '''
        pass

class DebugCParser(CParser):
    '''A convenience class that prints each invocation of a handle_* method to
    stdout.
    '''
    def handle_define(self, name, value):
        print '#define name=%r, value=%r' % (name, value)

    def handle_undef(self, name):
        print '#undef name=%r' % name

    def handle_if(self, expr):
        print '#if expr=%r' % expr
        super(DebugCParser, self).handle_if(expr)

    def handle_ifdef(self, name):
        print '#ifdef name=%r' % name
        super(DebugCParser, self).handle_ifdef(name)

    def handle_ifndef(self, name):
        print '#ifndef name=%r' % name
        super(DebugCParser, self).handle_ifndef(name)

    def handle_endif(self):
        print '#endif'
        super(DebugCParser, self).handle_endif()

    def handle_declaration(self, declaration):
        print declaration
        
if __name__ == '__main__':
    import sys
    file = sys.argv[1]
    DebugCParser().parse(open(file).read())
