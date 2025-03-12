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

import cPickle
import operator
import os.path
import re
import sys
import time
import warnings

import preprocessor
import yacc

tokens = (

    'PP_IF', 'PP_IFDEF', 'PP_IFNDEF', 'PP_ELIF', 'PP_ELSE',
    'PP_ENDIF', 'PP_INCLUDE', 'PP_DEFINE', 'PP_DEFINE_CONSTANT', 'PP_UNDEF',
    'PP_LINE', 'PP_ERROR', 'PP_PRAGMA',

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
    'CONTINUE', 'BREAK', 'RETURN', '__ASM__'
)

keywords = [
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
    'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'int',
    'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
    'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile',
    'while', '__asm__'
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

    # make pointer read-only to catch mistakes early
    pointer = property(lambda self: None)

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
        return ' '.join(self.qualifiers + [str(s) for s in self.specifiers])

# These are used only internally.

class StorageClassSpecifier(str):
    pass

class TypeSpecifier(str):
    pass

class StructTypeSpecifier(object):
    def __init__(self, is_union, tag, declarations):
        self.is_union = is_union
        self.tag = tag
        self.declarations = declarations

    def __repr__(self):
        if self.is_union:
            s = 'union'
        else:
            s = 'struct'
        if self.tag:
            s += ' %s' % self.tag
        if self.declarations:
            s += ' {%s}' % '; '.join([repr(d) for d in self.declarations])
        return s

class EnumSpecifier(object):
    def __init__(self, tag, enumerators):
        self.tag = tag
        self.enumerators = enumerators

    def __repr__(self):
        s = 'enum'
        if self.tag:
            s += ' %s' % self.tag
        if self.enumerators:
            s += ' {%s}' % ', '.join([repr(e) for e in self.enumerators])
        return s

class Enumerator(object):
    def __init__(self, name, expression):
        self.name = name
        self.expression = expression

    def __repr__(self):
        s = self.name
        if self.expression:
            s += ' = %r' % self.expression
        return s

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
        elif type(s) in (TypeSpecifier, StructTypeSpecifier, EnumSpecifier):
            declaration.type.specifiers.append(s)
        elif type(s) == TypeQualifier:
            declaration.type.qualifiers.append(s)


# --------------------------------------------------------------------------
# Expression Object Model
# --------------------------------------------------------------------------

class EvaluationContext(object):
    '''Interface for evaluating expression nodes.
    '''
    def evaluate_identifier(self, name):
        warnings.warn('Attempt to evaluate identifier "%s" failed' % name)
        return 0

    def evaluate_sizeof(self, type):
        warnings.warn('Attempt to evaluate sizeof "%s" failed' % str(type))
        return 0

class ExpressionNode(object):
    def evaluate(self, context):
        return 0

    def __str__(self):
        return ''

class ConstantExpressionNode(ExpressionNode):
    def __init__(self, value):
        self.value = value

    def evaluate(self, context):
        return self.value

    def __str__(self):
        return str(self.value)

class IdentifierExpressionNode(ExpressionNode):
    def __init__(self, name):
        self.name = name

    def evaluate(self, context):
        return context.evaluate_identifier(self.name)

    def __str__(self):
        return str(self.value)

class UnaryExpressionNode(ExpressionNode):
    def __init__(self, op, op_str, child):
        self.op = op
        self.op_str = op_str
        self.child = child

    def evaluate(self, context):
        return self.op(self.child.evaluate(context))

    def __str__(self):
        return '(%s %s)' % (self.op_str, self.child)

class SizeOfExpressionNode(ExpressionNode):
    def __init__(self, type):
        self.type = type

    def evaluate(self, context):
        return context.evaluate_sizeof(self.type)

    def __str__(self):
        return 'sizeof(%s)' % str(self.type)

class BinaryExpressionNode(ExpressionNode):
    def __init__(self, op, op_str, left, right):
        self.op = op
        self.op_str = op_str
        self.left = left
        self.right = right

    def evaluate(self, context):
        return self.op(self.left.evaluate(context), 
                       self.right.evaluate(context))

    def __str__(self):
        return '(%s %s %s)' % (self.left, self.op_str, self.right)

class LogicalAndExpressionNode(ExpressionNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def evaluate(self, context):
        return self.left.evaluate(context) and self.right.evaluate(context)

    def __str__(self):
        return '(%s && %s)' % (self.left, self.right)

class LogicalOrExpressionNode(ExpressionNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def evaluate(self, context):
        return self.left.evaluate(context) or self.right.evaluate(context)

    def __str__(self):
        return '(%s || %s)' % (self.left, self.right)

class ConditionalExpressionNode(ExpressionNode):
    def __init__(self, condition, left, right):
        self.condition = condition
        self.left = left
        self.right = right

    def evaluate(self, context):
        if self.condition.evaluate(context):
            return self.left.evaluate(context)
        else:
            return self.right.evaluate(context)

    def __str__(self):
        return '(%s ? %s : %s)' % (self.condition, self.left, self.right)


# --------------------------------------------------------------------------
# Grammar
# --------------------------------------------------------------------------

def p_translation_unit(p):
    '''translation_unit : 
                        | translation_unit external_declaration
    '''
    # Starting production.
    # Allow empty production so that files with no declarations are still
    #    valid.
    # Intentionally empty

def p_identifier(p):
    '''identifier : IDENTIFIER'''
    p[0] = IdentifierExpressionNode(p[1])

def p_constant(p):
    '''constant : CONSTANT
                | CHARACTER_CONSTANT
    '''
    def _to_int(s):
        s = s.rstrip('lLuU')
        if s.startswith('0x'):
            return int(s, base=16)
        elif s.startswith('0'):
            return int(s, base=8)
        else:
            return int(s)

    value = p[1]
    try:
        value = _to_int(value)
    except ValueError:
        pass
    p[0] = ConstantExpressionNode(value)

def p_string_literal(p):
    '''string_literal : STRING_LITERAL'''
    p[0] = ConstantExpressionNode(p[1])

def p_primary_expression(p):
    '''primary_expression : identifier
                          | constant
                          | string_literal
                          | '(' expression ')'
    '''
    if p[1] == '(':
        p[0] = p[2]
    else:
        p[0] = p[1]

def p_postfix_expression(p):
    '''postfix_expression : primary_expression
                  | postfix_expression '[' expression ']'
                  | postfix_expression '(' ')'
                  | postfix_expression '(' argument_expression_list ')'
                  | postfix_expression PERIOD IDENTIFIER
                  | postfix_expression PTR_OP IDENTIFIER
                  | postfix_expression INC_OP
                  | postfix_expression DEC_OP
    '''
    # XXX Largely unsupported
    p[0] = p[1]

def p_argument_expression_list(p):
    '''argument_expression_list : assignment_expression
                        | argument_expression_list ',' assignment_expression
    '''

def p_asm_expression(p):
    '''asm_expression : __ASM__ volatile_opt '(' string_literal ')'
                      | __ASM__ volatile_opt '(' string_literal ':' str_opt_expr_pair_list ')'
                      | __ASM__ volatile_opt '(' string_literal ':' str_opt_expr_pair_list ':' str_opt_expr_pair_list ')'
                      | __ASM__ volatile_opt '(' string_literal ':' str_opt_expr_pair_list ':' str_opt_expr_pair_list ':' str_opt_expr_pair_list ')'
    '''

    # Definitely not ISO C, adapted from example ANTLR GCC parser at
    #  http://www.antlr.org/grammar/cgram//grammars/GnuCParser.g
    # but more lenient (expressions permitted in optional final part, when
    # they shouldn't be -- avoids shift/reduce conflict with
    # str_opt_expr_pair_list).

    # XXX node not supported
    p[0] = ExpressionNode()

def p_str_opt_expr_pair_list(p):
    '''str_opt_expr_pair_list : 
                              | str_opt_expr_pair
                              | str_opt_expr_pair_list ',' str_opt_expr_pair
    '''

def p_str_opt_expr_pair(p):
   '''str_opt_expr_pair : string_literal
                        | string_literal '(' expression ')'
    '''

def p_volatile_opt(p):
    '''volatile_opt : 
                    | VOLATILE
    '''

def p_unary_expression(p):
    '''unary_expression : postfix_expression
                        | INC_OP unary_expression
                        | DEC_OP unary_expression
                        | unary_operator cast_expression
                        | SIZEOF unary_expression
                        | SIZEOF '(' type_name ')'
                        | asm_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif p[1] == 'sizeof':
        if p[2] == '(':
            p[0] = SizeOfExpressionNode(p[3])
        else:
            p[0] = SizeOfExpressionNode(p[2])
    elif type(p[1]) == tuple:
        # unary_operator reduces to (op, op_str)
        p[0] = UnaryExpressionNode(p[1][0], p[1][1], p[2])
    else:
        # XXX INC_OP and DEC_OP expression nodes not supported
        p[0] = p[2]

def p_unary_operator(p):
    '''unary_operator : '&'
                      | '*'
                      | '+'
                      | '-'
                      | '~'
                      | '!'
    '''
    # reduces to (op, op_str)
    p[0] = ({
        '+': operator.pos,
        '-': operator.neg,
        '~': operator.inv,
        '!': operator.not_,
        '&': 'AddressOfUnaryOperator',
        '*': 'DereferenceUnaryOperator'}[p[1]], p[1])

def p_cast_expression(p):
    '''cast_expression : unary_expression
                       | '(' type_name ')' cast_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        # XXX cast node not supported
        p[0] = p[4]

def p_multiplicative_expression(p):
    '''multiplicative_expression : cast_expression
                                 | multiplicative_expression '*' cast_expression
                                 | multiplicative_expression '/' cast_expression
                                 | multiplicative_expression '%' cast_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode({
            '*': operator.mul,
            '/': operator.div,
            '%': operator.mod}[p[2]], p[2], p[1], p[3])

def p_additive_expression(p):
    '''additive_expression : multiplicative_expression
                           | additive_expression '+' multiplicative_expression
                           | additive_expression '-' multiplicative_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode({
            '+': operator.add,
            '-': operator.sub}[p[2]], p[2], p[1], p[3])

def p_shift_expression(p):
    '''shift_expression : additive_expression
                        | shift_expression LEFT_OP additive_expression
                        | shift_expression RIGHT_OP additive_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode({
            '<<': operator.lshift,
            '>>': operator.rshift}[p[2]], p[2], p[1], p[3])
        
def p_relational_expression(p):
    '''relational_expression : shift_expression 
                             | relational_expression '<' shift_expression
                             | relational_expression '>' shift_expression
                             | relational_expression LE_OP shift_expression
                             | relational_expression GE_OP shift_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode({
            '>': operator.gt,
            '<': operator.lt,
            '<=': operator.le,
            '>=': operator.ge}[p[2]], p[2], p[1], p[3])

def p_equality_expression(p):
    '''equality_expression : relational_expression
                           | equality_expression EQ_OP relational_expression
                           | equality_expression NE_OP relational_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode({
            '==': operator.eq,
            '!=': operator.ne}[p[2]], p[2], p[1], p[3])

def p_and_expression(p):
    '''and_expression : equality_expression
                      | and_expression '&' equality_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode(operator.and_, '&', p[1], p[3])

def p_exclusive_or_expression(p):
    '''exclusive_or_expression : and_expression
                               | exclusive_or_expression '^' and_expression
    ''' 
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode(operator.xor, '^', p[1], p[3])

def p_inclusive_or_expression(p):
    '''inclusive_or_expression : exclusive_or_expression
                   | inclusive_or_expression '|' exclusive_or_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode(operator.or_, '|', p[1], p[3])

def p_logical_and_expression(p):
    '''logical_and_expression : inclusive_or_expression
                  | logical_and_expression AND_OP inclusive_or_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = LogicalAndExpressionNode(p[1], p[3])

def p_logical_or_expression(p):
    '''logical_or_expression : logical_and_expression
                  | logical_or_expression OR_OP logical_and_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = LogicalOrExpressionNode(p[1], p[3])


def p_conditional_expression(p):
    '''conditional_expression : logical_or_expression
          | logical_or_expression '?' expression ':' conditional_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ConditionalExpressionNode(p[1], p[3], p[5])

def p_assignment_expression(p):
    '''assignment_expression : conditional_expression
                 | unary_expression assignment_operator assignment_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        # XXX assignment expression node not supported
        p[0] = p[3]

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
    p[0] = p[1]
    # XXX sequence expression node not supported 

def p_constant_expression(p):
    '''constant_expression : conditional_expression
    '''
    p[0] = p[1]

def p_declaration(p):
    '''declaration : declaration_impl ';'
    '''
    # The ';' must be here, not in 'declaration', as declaration needs to
    # be executed before the ';' is shifted (otherwise the next lookahead will
    # be read, which may be affected by this declaration if its a typedef.

def p_declaration_impl(p):
    '''declaration_impl : declaration_specifiers
                        | declaration_specifiers init_declarator_list
    '''
    declaration = Declaration()
    apply_specifiers(p[1], declaration)

    if len(p) == 2:
        filename = p.slice[1].filename
        lineno = p.slice[1].lineno
        p.parser.cparser.impl_handle_declaration(declaration, filename, lineno)
        return

    filename = p.slice[2].filename
    lineno = p.slice[2].lineno
    for declarator in p[2]:
        declaration.declarator = declarator
        p.parser.cparser.impl_handle_declaration(declaration, filename, lineno)

""" # shift/reduce conflict with p_statement_error.
def p_declaration_error(p):
    '''declaration : error ';'
    '''
    # Error resynchronisation catch-all
"""

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
    if type(p[1]) in (StructTypeSpecifier, EnumSpecifier):
        p[0] = p[1]
    else:
        p[0] = TypeSpecifier(p[1])
    # TODO enum

def p_struct_or_union_specifier(p):
    '''struct_or_union_specifier : struct_or_union IDENTIFIER '{' struct_declaration_list '}'
         | struct_or_union TYPE_NAME '{' struct_declaration_list '}'
         | struct_or_union '{' struct_declaration_list '}'
         | struct_or_union IDENTIFIER
         | struct_or_union TYPE_NAME
    '''
    # The TYPE_NAME ones are dodgy, needed for Apple headers
    # CoreServices.framework/Frameworks/CarbonCore.framework/Headers/Files.h.
    # CoreServices.framework/Frameworks/OSServices.framework/Headers/Power.h
    if len(p) == 3:
        p[0] = StructTypeSpecifier(p[1], p[2], None)
    elif p[2] == '{':
        p[0] = StructTypeSpecifier(p[1], '', p[3])
    else:
        p[0] = StructTypeSpecifier(p[1], p[2], p[4])

def p_struct_or_union(p):
    '''struct_or_union : STRUCT
                       | UNION
    '''
    p[0] = p[1] == 'union'

def p_struct_declaration_list(p):
    '''struct_declaration_list : struct_declaration
                               | struct_declaration_list struct_declaration
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1] + p[2]

def p_struct_declaration(p):
    '''struct_declaration : specifier_qualifier_list struct_declarator_list ';'
    '''
    # p[0] returned is a tuple, to handle multiple declarators in one
    # declaration.
    r = ()
    for declarator in p[2]:
        declaration = Declaration()
        apply_specifiers(p[1], declaration)
        declaration.declarator = declarator
        r += (declaration,)
    p[0] = r

def p_specifier_qualifier_list(p):
    '''specifier_qualifier_list : type_specifier specifier_qualifier_list
                                | type_specifier
                                | type_qualifier specifier_qualifier_list
                                | type_qualifier
    '''
    # XXX Interesting.. why is this one right-recursion?
    if len(p) == 3:
        p[0] = (p[1],) + p[2]
    else:
        p[0] = (p[1],)

def p_struct_declarator_list(p):
    '''struct_declarator_list : struct_declarator
                              | struct_declarator_list ',' struct_declarator
    '''
    if len(p) == 2:
        p[0] = (p[1],)
    else:
        p[0] = p[1] + (p[3],)

def p_struct_declarator(p):
    '''struct_declarator : declarator
                         | ':' constant_expression
                         | declarator ':' constant_expression
    '''
    # XXX ignoring bitfields.
    if p[1] == ':':
        p[0] = Declarator()
    else:
        p[0] = p[1]

def p_enum_specifier(p):
    '''enum_specifier : ENUM '{' enumerator_list '}'
                      | ENUM IDENTIFIER '{' enumerator_list '}'
                      | ENUM IDENTIFIER
    '''
    if len(p) == 5:
        p[0] = EnumSpecifier(None, p[3])
    elif len(p) == 6:
        p[0] = EnumSpecifier(p[2], p[4])
    else:
        p[0] = EnumSpecifier(p[2], ())

def p_enumerator_list(p):
    '''enumerator_list : enumerator_list_iso
                       | enumerator_list_iso ','
    '''
    # Apple headers sometimes have trailing ',' after enumerants, which is
    # not ISO C.
    p[0] = p[1]

def p_enumerator_list_iso(p):
    '''enumerator_list_iso : enumerator
                           | enumerator_list_iso ',' enumerator
    '''
    if len(p) == 2:
        p[0] = (p[1],)
    else:
        p[0] = p[1] + (p[3],)

def p_enumerator(p):
    '''enumerator : IDENTIFIER
                  | IDENTIFIER '=' constant_expression
    '''
    if len(p) == 2:
        p[0] = Enumerator(p[1], None)
    else:
        p[0] = Enumerator(p[1], p[3])

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
                         | TYPE_NAME
                         | '(' declarator ')'
                         | direct_declarator '[' constant_expression ']'
                         | direct_declarator '[' ']'
                         | direct_declarator '(' parameter_type_list ')'
                         | direct_declarator '(' identifier_list ')'
                         | direct_declarator '(' ')'
    '''
    # TYPE_NAME path is because some types are predefined in wrapper scripts;
    # it is not valid C.

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

def p_type_name(p):
    '''type_name : specifier_qualifier_list
                 | specifier_qualifier_list abstract_declarator
    '''

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
            # Only if doesn't already terminate in a declarator
            if type(ptr) == Pointer:
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

def p_statement(p):
    '''statement : labeled_statement
                 | compound_statement
                 | expression_statement
                 | selection_statement
                 | iteration_statement
                 | jump_statement
    '''

def p_labeled_statement(p):
    '''labeled_statement : IDENTIFIER ':' statement
                         | CASE constant_expression ':' statement
                         | DEFAULT ':' statement
    '''

def p_compound_statement(p):
    '''compound_statement : '{' '}'
                          | '{' statement_list '}'
                          | '{' declaration_list '}'
                          | '{' declaration_list statement_list '}'
    '''

def p_compound_statement_error(p):
    '''compound_statement : '{' error '}'
    '''
    # Error resynchronisation catch-all

def p_declaration_list(p):
    '''declaration_list : declaration
                        | declaration_list declaration
    '''

def p_statement_list(p):
    '''statement_list : statement
                      | statement_list statement
    '''

def p_expression_statement(p):
    '''expression_statement : ';'
                            | expression ';'
    '''
def p_expression_statement_error(p):
    '''expression_statement : error ';'
    '''
    # Error resynchronisation catch-all

def p_selection_statement(p):
    '''selection_statement : IF '(' expression ')' statement
                           | IF '(' expression ')' statement ELSE statement
                           | SWITCH '(' expression ')' statement
    '''

def p_iteration_statement(p):
    '''iteration_statement : WHILE '(' expression ')' statement
    | DO statement WHILE '(' expression ')' ';'
    | FOR '(' expression_statement expression_statement ')' statement
    | FOR '(' expression_statement expression_statement expression ')' statement
    '''	

def p_jump_statement(p):
    '''jump_statement : GOTO IDENTIFIER ';'
                      | CONTINUE ';'
                      | BREAK ';'
                      | RETURN ';'
                      | RETURN expression ';'
    '''

def p_external_declaration(p):
    '''external_declaration : declaration 
                            | function_definition
    '''

    # Intentionally empty

def p_function_definition(p):
    '''function_definition : declaration_specifiers declarator declaration_list compound_statement
                        | declaration_specifiers declarator compound_statement
                        | declarator declaration_list compound_statement
                        | declarator compound_statement
    '''

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
        while self.pos < len(self.tokens):
            t = self.tokens[self.pos]
            self.pos += 1

            if not t:
                break

            # PP events
            if t.type == 'PP_DEFINE':
                name, value = t.value
                self.cparser.handle_define(
                    name, value, t.filename, t.lineno)
                continue
            elif t.type == 'PP_DEFINE_CONSTANT':
                name, value = t.value
                self.cparser.handle_define_constant(
                    name, value, t.filename, t.lineno)
                continue
            elif t.type == 'PP_IFNDEF':
                self.cparser.handle_ifndef(t.value, t.filename, t.lineno)
                continue
            # TODO: other PP tokens

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
        return None
        
# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------

class CPreprocessorParser(preprocessor.PreprocessorParser):
    def __init__(self, cparser, **kwargs):
        self.cparser = cparser
        preprocessor.PreprocessorParser.__init__(self, **kwargs)

    def push_file(self, filename, data=None):
        if not self.cparser.handle_include(filename):
            return

        tokens = self.cparser.get_cached_tokens(filename)
        if tokens is not None:
            self.output += tokens
            return

        if not data:
            data = open(filename).read()
        self.lexer.push_input(data, filename)

class CParser(object):
    '''Parse a C source file.

    Subclass and override the handle_* methods.  Call `parse` with a string
    to parse.
    '''
    def __init__(self, stddef_types=True, gnu_types=True, cache_headers=True):
        self.preprocessor_parser = CPreprocessorParser(self)
        self.parser = yacc.Parser()
        yacc.yacc(method='LALR').init_parser(self.parser)
        self.parser.cparser = self

        self.lexer = CLexer(self)
        if stddef_types:
            self.lexer.type_names.add('wchar_t')
            self.lexer.type_names.add('ptrdiff_t')
            self.lexer.type_names.add('size_t')
        if gnu_types:
            self.lexer.type_names.add('__builtin_va_list')
        if sys.platform == 'win32':
            self.lexer.type_names.add('__int64')

        self.header_cache = {}
        self.cache_headers = cache_headers
        self.load_header_cache()
    
    def parse(self, filename, data=None, debug=False):
        '''Parse a file.  Give filename or filename + data.

        If `debug` is True, parsing state is dumped to stdout.
        '''
        if not data:
            data = open(filename, 'r').read()
        
        self.handle_status('Preprocessing %s' % filename)
        self.preprocessor_parser.parse(filename, data, debug=debug)
        self.lexer.input(self.preprocessor_parser.output)
        self.handle_status('Parsing %s' % filename)
        self.parser.parse(lexer=self.lexer, debug=debug)

    def load_header_cache(self, filename=None):
        if not filename:
            filename = '.header.cache'
        try:
            self.header_cache = cPickle.load(open(filename, 'rb'))
            self.handle_status('Loaded header cache "%s".  Found:' % filename)
            for header in self.header_cache.keys():
                self.handle_status('  %s' % header)
        except:
            self.handle_status('Failed to load header cache "%s"' % filename)

    def save_header_cache(self, filename=None):
        if not filename:
            filename = '.header.cache'
        try:
            cPickle.dump(self.header_cache, open(filename, 'wb'))
            self.handle_status('Updated header cache "%s"' % filename)
        except:
            self.handle_status('Failed to update header cache "%s"' % filename)

    def get_cached_tokens(self, header):
        '''Return a list of tokens for `header`.

        If there is no cached copy, return None.
        '''
        try:
            now = os.stat(header).st_mtime
        except OSError:
            now = time.time()
        current_memento = self.preprocessor_parser.get_memento()
        if header in self.header_cache:
            timestamp, memento, tokens, namespace = self.header_cache[header]
            if self.preprocessor_parser.system_headers:
                self.handle_status('Not using cached header "%s" because ' \
                                   'of overridden system_headers.' % header)
            elif now < timestamp:
                self.handle_status('Not using cached header "%s" because ' \
                                   'cached copy is stale.' % header)
            elif memento != current_memento:
                self.handle_status('Not using cached header "%s" because ' \
                                   'memento differs.' % header)
            else:
                self.handle_status('Using cached header "%s"' % header)
                self.preprocessor_parser.namespace = namespace
                return tokens

        if self.cache_headers and not self.preprocessor_parser.system_headers:
            self.handle_status('Caching header "%s"' % header)
            self.cache_headers = False
            ppp = preprocessor.PreprocessorParser()
            ppp.include_path = self.preprocessor_parser.include_path
            ppp.parse(filename=header,
                      namespace=self.preprocessor_parser.namespace)
            self.header_cache[header] = (now, current_memento, 
                                         ppp.output, ppp.namespace.copy())
            self.save_header_cache()
            self.cache_headers = True
            return ppp.output

        return None

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

    def handle_status(self, message):
        '''Progress information.

        The default implementationg prints message to stderr.
        '''
        print >> sys.stderr, message

    def handle_include(self, header):
        '''#include `header`
        
        Return True to proceed with including the header, otherwise return
        False to skip it.  The default implementation returns True.
        '''
        return True

    def handle_define(self, name, value, filename, lineno):
        '''#define `name` `value` 

        both are strings, value could not be parsed as an expression
        '''

    def handle_define_constant(self, name, value, filename, lineno):
        '''#define `name` `value`

        value is an int or float
        '''

    def handle_undef(self, name):
        '''#undef `name`'''

    def handle_if(self, expr):
        '''#if `expr`'''

    def handle_ifdef(self, name):
        '''#ifdef `name`'''

    def handle_ifndef(self, name, filename, lineno):
        '''#ifndef `name`'''

    def handle_elif(self, expr):
        '''#elif `expr`'''

    def handle_else(self):
        '''#else'''

    def handle_endif(self):
        '''#endif'''

    def impl_handle_declaration(self, declaration, filename, lineno):
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
        self.handle_declaration(declaration, filename, lineno)

    def handle_declaration(self, declaration, filename, lineno):
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
        return True

    def handle_define(self, name, value, filename, lineno):
        print '#define name=%r, value=%r' % (name, value)

    def handle_define_constant(self, name, value, filename, lineno):
        print '#define constant name=%r, value=%r' % (name, value)

    def handle_undef(self, name):
        print '#undef name=%r' % name

    def handle_if(self, expr):
        print '#if expr=%s' % expr

    def handle_ifdef(self, name):
        print '#ifdef name=%r' % name

    def handle_ifndef(self, name, filename, lineno):
        print '#ifndef name=%r' % name

    def handle_elif(self, expr):
        print '#elif expr=%s' % expr

    def handle_else(self):
        print '#else'

    def handle_endif(self):
        print '#endif'

    def handle_declaration(self, declaration, filename, lineno):
        print declaration
        
if __name__ == '__main__':
    DebugCParser().parse(sys.argv[1], debug=True)
