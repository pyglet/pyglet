#!/usr/bin/env python

'''Parse a C source file.

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

import operator
import os.path
import re
import sys

import preprocessor
import yacc

tokens = (

    'PP_IF', 'PP_IFDEF', 'PP_IFNDEF', 'PP_ELIF', 'PP_ELSE',
    'PP_ENDIF', 'PP_INCLUDE', 'PP_DEFINE', 'PP_UNDEF', 'PP_LINE',
    'PP_ERROR', 'PP_PRAGMA',

    'IDENTIFIER', 'CONSTANT', 'CHARACTER_CONSTANT', 'STRING_LITERAL', 'SIZEOF',
    'PTR_OP', 'INC_OP', 'DEC_OP', 'LEFT_OP', 'RIGHT_OP', 'LE_OP', 'GE_OP',
    'EQ_OP', 'NE_OP', 'AND_OP', 'OR_OP', 'MUL_ASSIGN', 'DIV_ASSIGN',
    'MOD_ASSIGN', 'ADD_ASSIGN', 'SUB_ASSIGN', 'LEFT_ASSIGN', 'RIGHT_ASSIGN',
    'AND_ASSIGN', 'XOR_ASSIGN', 'OR_ASSIGN',  'HASH_HASH', 'PERIOD',
    'TYPE_NAME', 
    
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


# --------------------------------------------------------------------------
# C Object Model
# --------------------------------------------------------------------------

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
                    '???', p.lineno(1))
                return
            declaration.storage = s
        elif type(s) == TypeSpecifier:
            declaration.type.specifiers.append(s)
        elif type(s) == TypeQualifier:
            declaration.type.qualifiers.append(s)


# --------------------------------------------------------------------------
# Grammar
# --------------------------------------------------------------------------

def p_translation_unit(p):
    '''translation_unit : external_declaration
                        | translation_unit external_declaration
    '''
    # Starting production.
    # Intentionally empty

def p_identifier(p):
    '''identifier : IDENTIFIER'''

def p_constant(p):
    '''constant : CONSTANT
    '''

def p_string_literal(p):
    '''string_literal : STRING_LITERAL'''

def p_primary_expression(p):
    '''primary_expression : identifier
                          | constant
                          | string_literal
                          | '(' expression ')'
    '''

def p_postfix_expression(p):
    '''postfix_expression : primary_expression
                  | postfix_expression '[' expression ']'
                  | postfix_expression '(' ')'
                  | postfix_expression '(' argument_expression_list ')'
                  | postfix_expression '.' IDENTIFIER
                  | postfix_expression PTR_OP IDENTIFIER
                  | postfix_expression INC_OP
                  | postfix_expression DEC_OP
    '''

def p_argument_expression_list(p):
    '''argument_expression_list : assignment_expression
                        | argument_expression_list ',' assignment_expression
    '''

def p_unary_expression(p):
    '''unary_expression : postfix_expression
                        | INC_OP unary_expression
                        | DEC_OP unary_expression
                        | unary_operator cast_expression
                        | SIZEOF unary_expression
                        | SIZEOF '(' TYPE_NAME ')'
    '''

def p_unary_operator(p):
    '''unary_operator : '&'
                      | '*'
                      | '+'
                      | '-'
                      | '~'
                      | '!'
    '''

def p_cast_expression(p):
    '''cast_expression : unary_expression
                       | '(' TYPE_NAME ')' cast_expression
    '''

def p_multiplicative_expression(p):
    '''multiplicative_expression : cast_expression
                                 | multiplicative_expression '*' cast_expression
                                 | multiplicative_expression '/' cast_expression
                                 | multiplicative_expression '%' cast_expression
    '''

def p_additive_expression(p):
    '''additive_expression : multiplicative_expression
                           | additive_expression '+' multiplicative_expression
                           | additive_expression '-' multiplicative_expression
    '''

def p_shift_expression(p):
    '''shift_expression : additive_expression
                        | shift_expression LEFT_OP additive_expression
                        | shift_expression RIGHT_OP additive_expression
    '''

def p_relational_expression(p):
    '''relational_expression : shift_expression 
                             | relational_expression '<' shift_expression
                             | relational_expression '>' shift_expression
                             | relational_expression LE_OP shift_expression
                             | relational_expression GE_OP shift_expression
    '''

def p_equality_expression(p):
    '''equality_expression : relational_expression
                           | equality_expression EQ_OP relational_expression
                           | equality_expression NE_OP relational_expression
    '''

def p_and_expression(p):
    '''and_expression : equality_expression
                      | and_expression '&' equality_expression
    '''

def p_exclusive_or_expression(p):
    '''exclusive_or_expression : and_expression
                               | exclusive_or_expression '^' and_expression
    ''' 

def p_inclusive_or_expression(p):
    '''inclusive_or_expression : exclusive_or_expression
                       | inclusive_or_expression '|' exclusive_or_expression
    '''

def p_logical_and_expression(p):
    '''logical_and_expression : inclusive_or_expression
                      | logical_and_expression AND_OP inclusive_or_expression
    '''

def p_logical_or_expression(p):
    '''logical_or_expression : logical_and_expression
                      | logical_or_expression OR_OP logical_and_expression
    '''

def p_conditional_expression(p):
    '''conditional_expression : logical_or_expression
              | logical_or_expression '?' expression ':' conditional_expression
    '''

def p_assignment_expression(p):
    '''assignment_expression : conditional_expression
                 | unary_expression assignment_operator assignment_expression
    '''

def p_assignment_operator(p):
    '''assignment_operator : '='
                           | MUL_ASSIGN
                           | DIV_ASSIGN
                           | MOD_ASSIGN
                           | ADD_ASSIGN
                           | SUB_ASSIGN
                           | LEFT_ASSIGN
                           | RIGHT_ASSIGN
                           | AND_ASSIGN
                           | XOR_ASSIGN
                           | OR_ASSIGN
    '''

def p_expression(p):
    '''expression : assignment_expression
                  | expression ',' assignment_expression
    '''

def p_constant_expression(p):
    '''constant_expression : conditional_expression
    '''

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

    # ';' is being shifted now, so can accept PP again
    p.lexer.accept_preprocessor = True

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
                      | struct_or_union_specifier
                      | enum_specifier
                      | TYPE_NAME
    '''
    # Not handled: struct_or_union_specifier, enum_specifier
    p[0] = TypeSpecifier(p[1])

def p_struct_or_union_specifier(p):
    '''struct_or_union_specifier : struct_or_union IDENTIFIER '{' struct_declaration_list '}'
         | struct_or_union '{' struct_declaration_list '}'
         | struct_or_union IDENTIFIER
    '''

def p_struct_or_union(p):
    '''struct_or_union : STRUCT
                       | UNION
    '''

def p_struct_declaration_list(p):
    '''struct_declaration_list : struct_declaration
                               | struct_declaration_list struct_declaration
    '''

def p_struct_declaration(p):
    '''struct_declaration : specifier_qualifier_list struct_declarator_list ';'
    '''

def p_specifier_qualifier_list(p):
    '''specifier_qualifier_list : type_specifier specifier_qualifier_list
                                | type_specifier
                                | type_qualifier specifier_qualifier_list
                                | type_qualifier
    '''

def p_struct_declarator_list(p):
    '''struct_declarator_list : struct_declarator
                              | struct_declarator_list ',' struct_declarator
    '''

def p_struct_declarator(p):
    '''struct_declarator : declarator
                         | ':' constant_expression
                         | declarator ':' constant_expression
    '''

def p_enum_specifier(p):
    '''enum_specifier : ENUM '{' enumerator_list '}'
                      | ENUM IDENTIFIER '{' enumerator_list '}'
                      | ENUM IDENTIFIER
    '''

def p_enumerator_list(p):
    '''enumerator_list : enumerator
                       | enumerator_list ',' enumerator
    '''

def p_enumerator(p):
    '''enumerator : IDENTIFIER
                  | IDENTIFIER '=' constant_expression
    '''

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
            ptr.pointer = Declarator()
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

def p_external_declaration(p):
    '''external_declaration : declaration ';'
    '''
    # The ';' must be here, not in 'declaration', as declaration needs to
    # be executed before the ';' is shifted (otherwise the next lookahead will
    # be read, which may be affected by this declaration if its a typedef.

    # Not handled: function_definition
    # Intentionally empty

def p_error(t):
    if not t:
        # Crap, no way to get to CParser instance.  FIXME TODO
        print >> sys.stderr, 'Syntax error at end of file.'
    else:
        t.lexer.cparser.handle_error('Syntax error at %r' % t.value, 
             t.filename, t.lineno)
    # Don't alter lexer: default behaviour is to pass error production
    # up until it hits the catch-all at declaration, at which point
    # parsing continues (synchronisation).

# --------------------------------------------------------------------------
# Lexer
# --------------------------------------------------------------------------

class CLexer(object):
    def __init__(self, cparser):
        self.cparser = cparser
        self.type_names = set()

    def input(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def token(self):
        if self.pos < len(self.tokens):
            t = self.tokens[self.pos]
            self.pos += 1

            # Transform PP tokens into C tokens
            if t.type == 'LPAREN':
                t.type = '('
            elif t.type == 'PP_NUMBER':
                t.type = 'CONSTANT'
            elif t.type == 'IDENTIFIER' and t.value in keywords:
                t.type = t.value.upper()
            elif t.type == 'IDENTIFIER' and t.value in self.type_names:
                t.type = 'TYPE_NAME'
            t.lexer = self
            return t
        else:
            return None
        
# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------

class CParser(object):
    '''Parse a C source file.

    Subclass and override the handle_* methods.  Call `parse` with a string
    to parse.
    '''
    def __init__(self, stddef_types=True):
        self.parser = yacc.Parser()
        yacc.yacc(method='LALR').init_parser(self.parser)
        self.parser.cparser = self
        self.lexer = CLexer(self)

        if stddef_types:
            self.lexer.type_names.add('wchar_t')
            self.lexer.type_names.add('ptrdiff_t')
            self.lexer.type_names.add('size_t')
    
    def parse(self, tokens, debug=False):
        '''Parse a list of tokens returned from the preprocessor.

        If `debug` is True, parsing state is dumped to stdout.
        '''
        self.lexer.input(tokens)
        self.parser.parse(lexer=self.lexer, debug=debug)

    # ----------------------------------------------------------------------
    # Parser interface.  Override these methods in your subclass.
    # ----------------------------------------------------------------------

    def handle_error(self, message, filename, lineno):
        '''A parse error occured.  
        
        The default implementation prints `lineno` and `message` to stderr.
        The parser will try to recover from errors by synchronising at the
        next semicolon.
        '''
        print >> sys.stderr, '%s:%s %s' % (filename, lineno, message)

    def handle_missing_header(self, header):
        '''A header was included that can't be located.

        Default implementation prints a warning to stderr.
        '''
        print >> sys.stderr, 'Could not find header %s' % header

    def handle_include(self, header):
        '''#include `header`'''
        if type(header) == StringLiteral:
            self.include(self.get_local_header(header), header)
        else:
            self.include(self.get_system_header(header), header)

    def handle_define(self, name, value):
        '''#define `name` `value` (both are strings)'''
        self.preprocessor_context.macros[name] = value

    def handle_undef(self, name):
        '''#undef `name`'''
        if name in self.preprocessor_context.macros:
            del self.preprocessor_context.macros[name]

    def handle_if(self, expr):
        '''#if `expr`'''
        self.apply_conditional(expr.evaluate(self.preprocessor_context))

    def handle_ifdef(self, name):
        '''#ifdef `name`'''
        self.apply_conditional(self.preprocessor_context.is_defined(name))

    def handle_ifndef(self, name):
        '''#ifndef `name`'''
        self.apply_conditional(not self.preprocessor_context.is_defined(name))

    def handle_elif(self, expr):
        '''#elif `expr`'''
        self.apply_conditional_elif(expr.evaluate(self.preprocessor_context))

    def handle_else(self):
        '''#else'''
        self.apply_conditional_else()

    def handle_endif(self):
        '''#endif'''
        self.apply_conditional_endif()

    def impl_handle_declaration(self, declaration):
        '''Internal method that calls `handle_declaration`.  This method
        also adds any new type definitions to the lexer's list of valid type
        names, which affects the parsing of subsequent declarations.
        '''
        if declaration.storage == 'typedef':
            declarator = declaration.declarator
            if not declarator:
                # XXX TEMPORARY while struct etc not filled
                return
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
    def handle_include(self, header):
        print '#include header=%r' % header
        super(DebugCParser, self).handle_include(header)

    def handle_define(self, name, value):
        print '#define name=%r, value=%r' % (name, value)
        super(DebugCParser, self).handle_define(name, value)

    def handle_undef(self, name):
        print '#undef name=%r' % name
        super(DebugCParser, self).handle_undef(name)

    def handle_if(self, expr):
        print '#if expr=%s' % expr
        super(DebugCParser, self).handle_if(expr)

    def handle_ifdef(self, name):
        print '#ifdef name=%r' % name
        super(DebugCParser, self).handle_ifdef(name)

    def handle_ifndef(self, name):
        print '#ifndef name=%r' % name
        super(DebugCParser, self).handle_ifndef(name)

    def handle_elif(self, expr):
        print '#elif expr=%s' % expr
        super(DebugCParser, self).handle_elif(expr)

    def handle_else(self):
        print '#else'
        super(DebugCParser, self).handle_else()

    def handle_endif(self):
        print '#endif'
        super(DebugCParser, self).handle_endif()

    def handle_declaration(self, declaration):
        print declaration
        
if __name__ == '__main__':
    import sys
    pp = preprocessor.PreprocessorParser('ppcache.py')
    pp.cache('Carbon/Carbon.h')
    pp.cache('X11/Xlib.h')
    pp.cache('windows.h')
    pp.parse(filename=sys.argv[1], debug=True)
    DebugCParser().parse(pp.output, debug=1)
