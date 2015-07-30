#!/usr/bin/env python

'''Preprocess a C source file.

Limitations:

  * Whitespace is not preserved.
  * # and ## operators not handled.

Reference is C99:
  * http://www.open-std.org/JTC1/SC22/WG14/www/docs/n1124.pdf
  * Also understands Objective-C #import directive
  * Also understands GNU #include_next

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import operator
import os.path
import cPickle
import re
import sys

import lex
from lex import TOKEN
import yacc

tokens = (
    'HEADER_NAME', 'IDENTIFIER', 'PP_NUMBER', 'CHARACTER_CONSTANT',
    'STRING_LITERAL', 'OTHER',

    'PTR_OP', 'INC_OP', 'DEC_OP', 'LEFT_OP', 'RIGHT_OP', 'LE_OP', 'GE_OP',
    'EQ_OP', 'NE_OP', 'AND_OP', 'OR_OP', 'MUL_ASSIGN', 'DIV_ASSIGN',
    'MOD_ASSIGN', 'ADD_ASSIGN', 'SUB_ASSIGN', 'LEFT_ASSIGN', 'RIGHT_ASSIGN',
    'AND_ASSIGN', 'XOR_ASSIGN', 'OR_ASSIGN',  'HASH_HASH', 'PERIOD',
    'ELLIPSIS',

    'IF', 'IFDEF', 'IFNDEF', 'ELIF', 'ELSE', 'ENDIF', 'INCLUDE',
    'INCLUDE_NEXT', 'DEFINE', 'UNDEF', 'LINE', 'ERROR', 'PRAGMA', 'DEFINED',
    'IMPORT',

    'NEWLINE', 'LPAREN'
)

subs = {
    'D': '[0-9]',
    'L': '[a-zA-Z_]',
    'H': '[a-fA-F0-9]',
    'E': '[Ee][+-]?{D}+',
    'FS': '[FflL]',
    'IS': '[uUlL]*',
}
# Helper: substitute {foo} with subs[foo] in string (makes regexes more lexy)
sub_pattern = re.compile('{([^}]*)}')
def sub_repl_match(m):
    return subs[m.groups()[0]]
def sub(s):
    return sub_pattern.sub(sub_repl_match, s)
CHARACTER_CONSTANT = sub(r"L?'(\\.|[^\\'])+'")
STRING_LITERAL = sub(r'L?"(\\.|[^\\"])*"')
IDENTIFIER = sub('{L}({L}|{D})*')

# --------------------------------------------------------------------------
# Token value types
# --------------------------------------------------------------------------

# Numbers represented as int and float types.
# For all other tokens, type is just str representation.

class StringLiteral(str):
    def __new__(cls, value):
        assert value[0] == '"' and value[-1] == '"'
        # Unescaping probably not perfect but close enough.
        value = value[1:-1].decode('string_escape')
        return str.__new__(cls, value)

class SystemHeaderName(str):
    def __new__(cls, value):
        assert value[0] == '<' and value[-1] == '>'
        return str.__new__(cls, value[1:-1])

    def __repr__(self):
        return '<%s>' % (str(self))


# --------------------------------------------------------------------------
# Token declarations
# --------------------------------------------------------------------------

punctuators = {
    # value: (regex, type)
    r'>>=': (r'>>=', 'RIGHT_ASSIGN'),
    r'<<=': (r'<<=', 'LEFT_ASSIGN'),
    r'+=': (r'\+=', 'ADD_ASSIGN'),
    r'-=': (r'-=', 'SUB_ASSIGN'),
    r'*=': (r'\*=', 'MUL_ASSIGN'),
    r'/=': (r'/=', 'DIV_ASSIGN'),
    r'%=': (r'%=', 'MOD_ASSIGN'),
    r'&=': (r'&=', 'AND_ASSIGN'),
    r'^=': (r'\^=', 'XOR_ASSIGN'),
    r'|=': (r'\|=', 'OR_ASSIGN'),
    r'>>': (r'>>', 'RIGHT_OP'),
    r'<<': (r'<<', 'LEFT_OP'),
    r'++': (r'\+\+', 'INC_OP'),
    r'--': (r'--', 'DEC_OP'),
    r'->': (r'->', 'PTR_OP'),
    r'&&': (r'&&', 'AND_OP'),
    r'||': (r'\|\|', 'OR_OP'),
    r'<=': (r'<=', 'LE_OP'),
    r'>=': (r'>=', 'GE_OP'),
    r'==': (r'==', 'EQ_OP'),
    r'!=': (r'!=', 'NE_OP'),
    r'<:': (r'<:', '['),
    r':>': (r':>', ']'),
    r'<%': (r'<%', '{'),
    r'%>': (r'%>', '}'),
    r'%:%:': (r'%:%:', 'HASH_HASH'),
    r';': (r';', ';'),
    r'{': (r'{', '{'),
    r'}': (r'}', '}'),
    r',': (r',', ','),
    r':': (r':', ':'),
    r'=': (r'=', '='),
    r')': (r'\)', ')'),
    r'[': (r'\[', '['),
    r']': (r']', ']'),
    r'.': (r'\.', 'PERIOD'),
    r'&': (r'&', '&'),
    r'!': (r'!', '!'),
    r'~': (r'~', '~'),
    r'-': (r'-', '-'),
    r'+': (r'\+', '+'),
    r'*': (r'\*', '*'),
    r'/': (r'/', '/'),
    r'%': (r'%', '%'),
    r'<': (r'<', '<'),
    r'>': (r'>', '>'),
    r'^': (r'\^', '^'),
    r'|': (r'\|', '|'),
    r'?': (r'\?', '?'),
    r'#': (r'\#', '#'),
}

def punctuator_regex(punctuators):
    punctuator_regexes = [v[0] for v in punctuators.values()]
    punctuator_regexes.sort(lambda a, b: -cmp(len(a), len(b)))
    return '(%s)' % '|'.join(punctuator_regexes)

def t_clinecomment(t):
    r'//[^\n]*'
    t.lexer.lineno += 1

def t_cr(t):
    r'\r'
    # Skip over CR characters.  Only necessary on urlopen'd files.

# C /* comments */.  Copied from the ylex.py example in PLY: it's not 100%
# correct for ANSI C, but close enough for anything that's not crazy.
def t_ccomment(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

def t_header_name(t):
    r'<([\/]?[^\/\*\n>])*[\/]?>(?=[ \t\f\v\r\n])'
    # Should allow any character from charset, but that wreaks havok (skips
    #   comment delimiter, for instance), so also don't permit '*' or '//'
    # The non-matching group at the end prevents false-positives with
    #   operators like '>='.
    # In the event of a false positive (e.g. "if (a < b || c > d)"), the
    #  token will be split and rescanned if it appears in a text production;
    #  see PreprocessorParser.write.
    # Is also r'"[^\n"]"', but handled in STRING_LITERAL instead.
    t.type = 'HEADER_NAME'
    t.value = SystemHeaderName(t.value)
    return t

def t_directive(t):
    r'\#[ \t]*(ifdef|ifndef|if|elif|else|endif|define|undef|include_next|include|import|line|error|pragma)'
    if t.lexer.lasttoken in ('NEWLINE', None):
        t.type = t.value[1:].lstrip().upper()
    else:
        # TODO
        t.type = '#'
        t.lexer.nexttoken = ('IDENTIFIER', t.value[1:].lstrip())
    return t

@TOKEN(r'(' + IDENTIFIER + r')?\.\.\.')
def t_ellipsis(t):
    """In GNU C ellipsis can be prepended with a variable name, so not simply punctuation."""
    t.type = 'ELLIPSIS'
    return t

@TOKEN(punctuator_regex(punctuators))
def t_punctuator(t):
    t.type = punctuators[t.value][1]
    return t

@TOKEN(CHARACTER_CONSTANT)
def t_character_constant(t):
    t.type = 'CHARACTER_CONSTANT'
    return t

@TOKEN(IDENTIFIER)
def t_identifier(t):
    if t.value == 'defined':
        t.type = 'DEFINED'
    else:
        t.type = 'IDENTIFIER'
    return t

    # missing: universal-character-constant
@TOKEN(sub(r'({D}|\.{D})({D}|{L}|e[+-]|E[+-]|p[+-]|P[+-]|\.)*'))
def t_pp_number(t):
    t.type = 'PP_NUMBER'
    return t
    
@TOKEN(STRING_LITERAL)
def t_string_literal(t):
    t.type = 'STRING_LITERAL'
    t.value = StringLiteral(t.value)
    return t

def t_lparen(t):
    r'\('
    if t.lexpos == 0 or t.lexer.lexdata[t.lexpos-1] not in (' \t\f\v\n'):
        t.type = 'LPAREN'
    else:
        t.type = '('
    return t

def t_continuation(t):
    r'\\\n'
    t.lexer.lineno += 1
    return None

def t_newline(t):
    r'\n'
    t.lexer.lineno += 1
    t.type = 'NEWLINE'
    return t

def t_error(t):
    t.type = 'OTHER'
    return t

t_ignore = ' \t\v\f'

# --------------------------------------------------------------------------
# Expression Object Model
# --------------------------------------------------------------------------

class EvaluationContext(object):
    '''Interface for evaluating expression nodes.
    '''
    def is_defined(self, identifier):
        return False

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

class UnaryExpressionNode(ExpressionNode):
    def __init__(self, op, op_str, child):
        self.op = op
        self.op_str = op_str
        self.child = child

    def evaluate(self, context):
        return self.op(self.child.evaluate(context))

    def __str__(self):
        return '(%s %s)' % (self.op_str, self.child)

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
# Lexers
# --------------------------------------------------------------------------

class PreprocessorLexer(lex.Lexer):
    def __init__(self):
        lex.Lexer.__init__(self)
        self.filename = '<input>'

    def input(self, data, filename=None):
        if filename:
            self.filename = filename 
        self.lasttoken = None
        self.input_stack = []

        lex.Lexer.input(self, data)

    def push_input(self, data, filename):
        self.input_stack.append(
            (self.lexdata, self.lexpos, self.filename, self.lineno))
        self.lexdata = data
        self.lexpos = 0
        self.lineno = 1
        self.filename = filename
        self.lexlen = len(self.lexdata)

    def pop_input(self):
        self.lexdata, self.lexpos, self.filename, self.lineno = \
            self.input_stack.pop()
        self.lexlen = len(self.lexdata)

    def token(self):
        result = lex.Lexer.token(self)
        while result is None and self.input_stack:
            self.pop_input()
            result = lex.Lexer.token(self)

        if result:
            self.lasttoken = result.type
            result.filename = self.filename
        else:
            self.lasttoken = None

        return result

class TokenListLexer(object):
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def token(self):
        if self.pos < len(self.tokens):
            t = self.tokens[self.pos]
            self.pos += 1
            return t
        else:
            return None

def symbol_to_token(sym):
    if isinstance(sym, yacc.YaccSymbol):
        return sym.value
    elif isinstance(sym, lex.LexToken):
        return sym
    else:
        assert False, 'Not a symbol: %r' % sym

def create_token(type, value, production=None):
    '''Create a token of type and value, at the position where 'production'
    was reduced.  Don't specify production if the token is built-in'''
    t = lex.LexToken()
    t.type = type
    t.value = value
    t.lexpos = -1
    if production:
        t.lineno = production.slice[1].lineno
        t.filename = production.slice[1].filename
    else:
        t.lineno = -1
        t.filename = '<builtin>'
    return t

# --------------------------------------------------------------------------
# Grammars
# --------------------------------------------------------------------------

class Grammar(object):
    prototype = None
    name = 'grammar'

    @classmethod
    def get_prototype(cls):
        if not cls.prototype:
            instance = cls()
            tabmodule = '%stab' % cls.name
            cls.prototype = yacc.yacc(module=instance, tabmodule=tabmodule)
        return cls.prototype

class PreprocessorGrammar(Grammar):
    tokens = tokens
    name = 'pp'

    def p_preprocessing_file(self, p):
        '''preprocessing_file : group_opt
        '''

    def p_group_opt(self, p):
        '''group_opt : group
                     | 
        '''

    def p_group(self, p):
        '''group : group_part
                 | group group_part
        '''

    def p_group_part(self, p):
        '''group_part : if_section
                      | control_line
                      | text_line
        '''

    def p_if_section(self, p):
        '''if_section : if_group elif_groups_opt else_group_opt endif_line
        '''

    def p_if_group(self, p):
        '''if_group : if_line group_opt
        '''

    def p_if_line(self, p):
        '''if_line : IF replaced_constant_expression NEWLINE
                   | IFDEF IDENTIFIER NEWLINE
                   | IFNDEF IDENTIFIER NEWLINE 
        '''
        if p.parser.enable_declaratives():
            type = p.slice[1].type
            if type == 'IF':
                if p[2]:
                    result = p[2].evaluate(p.parser.namespace)
                else:
                    # error
                    result = False
            elif type == 'IFDEF':
                result = p.parser.namespace.is_defined(p[2])
            elif type == 'IFNDEF':
                result = not p.parser.namespace.is_defined(p[2])
                p.parser.write((create_token('PP_IFNDEF', p[2], p),))
        else:
            result = False
        
        p.parser.condition_if(result)

    def p_elif_groups_opt(self, p):
        '''elif_groups_opt : elif_groups
                           |
        '''

    def p_elif_groups(self, p):
        '''elif_groups : elif_group
                       | elif_groups elif_group
        '''

    def p_elif_group(self, p):
        '''elif_group : elif_line group_opt
        '''

    def p_elif_line(self, p):
        '''elif_line : ELIF replaced_elif_constant_expression NEWLINE
        '''
        result = p[2].evaluate(p.parser.namespace)
        p.parser.condition_elif(result)

    def p_else_group_opt(self, p):
        '''else_group_opt : else_group
                          |
        '''

    def p_else_group(self, p):
        '''else_group : else_line group_opt
        '''

    def p_else_line(self, p):
        '''else_line : ELSE NEWLINE
        '''
        p.parser.condition_else()

    def p_endif_line(self, p):
        '''endif_line : ENDIF pp_tokens_opt NEWLINE
        '''
        # pp_tokens needed (ignored) here for Apple.
        p.parser.condition_endif()

    def p_control_line(self, p):
        '''control_line : include_line NEWLINE
                        | define_object
                        | define_function
                        | undef_line
                        | LINE pp_tokens NEWLINE
                        | error_line
                        | PRAGMA pp_tokens_opt NEWLINE
        '''

    def p_include_line(self, p):
        '''include_line : INCLUDE pp_tokens 
                        | INCLUDE_NEXT pp_tokens
                        | IMPORT pp_tokens
        '''
        if p.parser.enable_declaratives():
            tokens = p[2]
            tokens = p.parser.namespace.apply_macros(tokens)
            if len(tokens) > 0:
                if p.slice[1].type == 'INCLUDE':
                    if tokens[0].type == 'STRING_LITERAL':
                        p.parser.include(tokens[0].value)
                        return
                    elif tokens[0].type == 'HEADER_NAME':
                        p.parser.include_system(tokens[0].value)
                        return
                elif p.slice[1].type == 'INCLUDE_NEXT':
                    p.parser.include_next(tokens[0].value, p.slice[1].filename)
                    return
                else:
                    if tokens[0].type == 'STRING_LITERAL':
                        p.parser.import_(tokens[0].value)
                        return
                    elif tokens[0].type == 'HEADER_NAME':
                        p.parser.import_system(tokens[0].value)
                        return

            # TODO
            print >> sys.stderr, 'Invalid #include'

    def p_define_object(self, p):
        '''define_object : DEFINE IDENTIFIER replacement_list NEWLINE 
        '''
        if p.parser.enable_declaratives():
            p.parser.namespace.define_object(p[2], p[3])

            # Try to parse replacement list as an expression
            tokens = p.parser.namespace.apply_macros(p[3])
            lexer = TokenListLexer(tokens)
            expr_parser = StrictConstantExpressionParser(lexer, 
                                                         p.parser.namespace)
            value = expr_parser.parse(debug=False)
            if value is not None:
                value = value.evaluate(p.parser.namespace)
                p.parser.write(
                    (create_token('PP_DEFINE_CONSTANT', (p[2], value), p),))
            else:
                # Didn't parse, pass on as string
                value = ' '.join([str(t.value) for t in p[3]])
                p.parser.write((create_token('PP_DEFINE', (p[2], value), p),))

    def p_define_function(self, p):
        '''define_function : DEFINE IDENTIFIER LPAREN define_function_params ')' pp_tokens_opt NEWLINE
        '''
        if p.parser.enable_declaratives():
            p.parser.namespace.define_function(p[2], p[4], p[6])

    def p_define_function_params(self, p):
        '''define_function_params : identifier_list_opt
                                  | ELLIPSIS
                                  | identifier_list ',' ELLIPSIS
        '''
        if len(p) == 2:
            if p[1] == 'ELLIPSIS':
                p[0] = ('...',)
            else:
                p[0] = p[1]
        else:
            p[0] = p[1] + ('...',)

    def p_undef_line(self, p):
        '''undef_line : UNDEF IDENTIFIER NEWLINE
        '''
        if p.parser.enable_declaratives():
            p.parser.namespace.undef(p[2])

    def p_error_line(self, p):
        '''error_line : ERROR pp_tokens_opt NEWLINE
        '''
        if p.parser.enable_declaratives():
            p.parser.error(' '.join([t.value for t in p[2]]), 
                           p.slice[1].filename, p.slice[1].lineno)

    def p_text_line(self, p):
        '''text_line : pp_tokens_opt NEWLINE
        '''
        if p.parser.enable_declaratives():
            tokens = p[1]
            tokens = p.parser.namespace.apply_macros(tokens)
            p.parser.write(tokens)

    def p_replacement_list(self, p):
        '''replacement_list : 
                            | preprocessing_token_no_lparen
                            | preprocessing_token_no_lparen pp_tokens
        '''
        if len(p) == 3:
            p[0] = (p[1],) + p[2]
        elif len(p) == 2:
            p[0] = (p[1],)
        else:
            p[0] = ()

    def p_identifier_list_opt(self, p):
        '''identifier_list_opt : identifier_list
                               | 
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ()

    def p_identifier_list(self, p):
        '''identifier_list : IDENTIFIER
                           | identifier_list ',' IDENTIFIER
        '''
        if len(p) > 2:
            p[0] = p[1] + (p[3],)
        else:
            p[0] = (p[1],)

    def p_replaced_constant_expression(self, p):
        '''replaced_constant_expression : pp_tokens'''
        if p.parser.enable_conditionals():
            tokens = p[1]
            tokens = p.parser.namespace.apply_macros(tokens)
            lexer = TokenListLexer(tokens)
            parser = ConstantExpressionParser(lexer, p.parser.namespace) 
            p[0] = parser.parse(debug=True)
        else:
            p[0] = ConstantExpressionNode(0)

    def p_replaced_elif_constant_expression(self, p):
        '''replaced_elif_constant_expression : pp_tokens'''
        if p.parser.enable_elif_conditionals():
            tokens = p[1]
            tokens = p.parser.namespace.apply_macros(tokens)
            lexer = TokenListLexer(tokens)
            parser = ConstantExpressionParser(lexer, p.parser.namespace) 
            p[0] = parser.parse(debug=True)
        else:
            p[0] = ConstantExpressionNode(0)


    def p_pp_tokens_opt(self, p):
        '''pp_tokens_opt : pp_tokens
                         |  
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ()

    def p_pp_tokens(self, p):
        '''pp_tokens : preprocessing_token
                     | pp_tokens preprocessing_token
        '''
        if len(p) == 2:
            p[0] = (p[1],)
        else:
            p[0] = p[1] + (p[2],)

    def p_preprocessing_token_no_lparen(self, p):
        '''preprocessing_token_no_lparen : HEADER_NAME
                                         | IDENTIFIER
                                         | PP_NUMBER
                                         | CHARACTER_CONSTANT
                                         | STRING_LITERAL
                                         | punctuator
                                         | DEFINED
                                         | OTHER
        '''
        p[0] = symbol_to_token(p.slice[1])

    def p_preprocessing_token(self, p):
        '''preprocessing_token : preprocessing_token_no_lparen
                               | LPAREN
        '''
        p[0] = symbol_to_token(p.slice[1])

    def p_punctuator(self, p):
        '''punctuator : ELLIPSIS 
                      | RIGHT_ASSIGN 
                      | LEFT_ASSIGN 
                      | ADD_ASSIGN
                      | SUB_ASSIGN 
                      | MUL_ASSIGN 
                      | DIV_ASSIGN 
                      | MOD_ASSIGN 
                      | AND_ASSIGN 
                      | XOR_ASSIGN 
                      | OR_ASSIGN 
                      | RIGHT_OP 
                      | LEFT_OP 
                      | INC_OP 
                      | DEC_OP 
                      | PTR_OP 
                      | AND_OP 
                      | OR_OP 
                      | LE_OP 
                      | GE_OP
                      | EQ_OP 
                      | NE_OP 
                      | HASH_HASH 
                      | ';' 
                      | '{' 
                      | '}' 
                      | ',' 
                      | ':' 
                      | '=' 
                      | '(' 
                      | ')' 
                      | '[' 
                      | ']' 
                      | PERIOD
                      | '&' 
                      | '!' 
                      | '~' 
                      | '-'
                      | '+' 
                      | '*' 
                      | '/' 
                      | '%' 
                      | '<' 
                      | '>' 
                      | '^' 
                      | '|' 
                      | '?' 
                      | '#'
        '''
        p[0] = symbol_to_token(p.slice[1])

    def p_error(self, t):
        if not t:
            # Crap, no way to get to Parser instance.  FIXME TODO
            print >> sys.stderr, 'Syntax error at end of file.'
        else:
            # TODO
            print >> sys.stderr, '%s:%d Syntax error at %r' % \
                (t.lexer.filename, t.lexer.lineno, t.value)
            #t.lexer.cparser.handle_error('Syntax error at %r' % t.value, 
            #     t.lexer.filename, t.lexer.lineno)
        # Don't alter lexer: default behaviour is to pass error production
        # up until it hits the catch-all at declaration, at which point
        # parsing continues (synchronisation).

class ConstantExpressionParseException(Exception):
    pass

class ConstantExpressionGrammar(Grammar):
    name = 'expr'
    tokens = tokens

    def p_constant_expression(self, p):
        '''constant_expression : conditional_expression
        '''
        p[0] = p[1]
        p.parser.result = p[0]

    def p_character_constant(self, p):
        '''character_constant : CHARACTER_CONSTANT
        '''
        try:
            value = ord(eval(p[1].lstrip('L')))
        except StandardError:
            value = 0
        p[0] = ConstantExpressionNode(value)

    def p_constant(self, p):
        '''constant : PP_NUMBER
        '''
        value = p[1].rstrip('LlUu')
        try:
            if value[:2] == '0x':
                value = int(value[2:], 16)
            elif value[0] == '0':
                value = int(value, 8)
            else:
                value = int(value)
        except ValueError:
            value = value.rstrip('eEfF')
            try:
                value = float(value)
            except ValueError:
                value = 0
        p[0] = ConstantExpressionNode(value)

    def p_identifier(self, p):
        '''identifier : IDENTIFIER
        '''
        p[0] = ConstantExpressionNode(0)

    def p_primary_expression(self, p):
        '''primary_expression : constant
                              | character_constant
                              | identifier
                              | '(' expression ')'
                              | LPAREN expression ')'
        '''
        if p[1] == '(':
            p[0] = p[2]
        else:
            p[0] = p[1]

    def p_postfix_expression(self, p):
        '''postfix_expression : primary_expression
        '''
        p[0] = p[1]
        
    def p_unary_expression(self, p):
        '''unary_expression : postfix_expression
                            | unary_operator cast_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        elif type(p[1]) == tuple:
            # unary_operator reduces to (op, op_str)
            p[0] = UnaryExpressionNode(p[1][0], p[1][1], p[2])
        else:
            # TODO
            p[0] = None

    def p_unary_operator(self, p):
        '''unary_operator : '+'
                          | '-'
                          | '~'
                          | '!'
        '''
        # reduces to (op, op_str)
        p[0] = ({
            '+': operator.pos,
            '-': operator.neg,
            '~': operator.inv,
            '!': operator.not_}[p[1]], p[1])

    def p_cast_expression(self, p):
        '''cast_expression : unary_expression
        '''
        p[0] = p[len(p) - 1]

    def p_multiplicative_expression(self, p):
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

    def p_additive_expression(self, p):
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

    def p_shift_expression(self, p):
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

    def p_relational_expression(self, p):
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

    def p_equality_expression(self, p):
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

    def p_and_expression(self, p):
        '''and_expression : equality_expression
                          | and_expression '&' equality_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExpressionNode(operator.and_, '&', p[1], p[3])

    def p_exclusive_or_expression(self, p):
        '''exclusive_or_expression : and_expression
                                   | exclusive_or_expression '^' and_expression
        ''' 
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExpressionNode(operator.xor, '^', p[1], p[3])

    def p_inclusive_or_expression(self, p):
        '''inclusive_or_expression : exclusive_or_expression
                       | inclusive_or_expression '|' exclusive_or_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryExpressionNode(operator.or_, '|', p[1], p[3])

    def p_logical_and_expression(self, p):
        '''logical_and_expression : inclusive_or_expression
                      | logical_and_expression AND_OP inclusive_or_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = LogicalAndExpressionNode(p[1], p[3])

    def p_logical_or_expression(self, p):
        '''logical_or_expression : logical_and_expression
                      | logical_or_expression OR_OP logical_and_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = LogicalOrExpressionNode(p[1], p[3])


    def p_conditional_expression(self, p):
        '''conditional_expression : logical_or_expression
              | logical_or_expression '?' expression ':' conditional_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ConditionalExpressionNode(p[1], p[3], p[5])

    def p_assignment_expression(self, p):
        '''assignment_expression : conditional_expression
                 | unary_expression assignment_operator assignment_expression
        '''
        # TODO assignment
        if len(p) == 2:
            p[0] = p[1]

    def p_assignment_operator(self, p):
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

    def p_expression(self, p):
        '''expression : assignment_expression
                      | expression ',' assignment_expression
        '''
        # TODO sequence
        if len(p) == 2:
            p[0] = p[1]

    def p_error(self, t):
        raise ConstantExpressionParseException()

class StrictConstantExpressionGrammar(ConstantExpressionGrammar):
    name = 'strict_expr'
    tokens = tokens

    def p_identifier(self, p):
        '''identifier : IDENTIFIER
        '''
        raise ConstantExpressionParseException()

class ExecutionState(object):
    def __init__(self, parent_enabled, enabled):
        self.enabled = parent_enabled and enabled
        self.context_enabled = enabled
        self.parent_enabled = parent_enabled

    def enable(self, result):
        if result:
            self.enabled = self.parent_enabled and not self.context_enabled
            self.context_enabled = True
        else:
            self.enabled = False

class PreprocessorParser(yacc.Parser):
    def __init__(self, gcc_search_path=True):
        yacc.Parser.__init__(self)
        self.lexer = lex.lex(cls=PreprocessorLexer)
        PreprocessorGrammar.get_prototype().init_parser(self)

        # Map system header name to data, overrides path search and open()
        self.system_headers = {}


        self.include_path = ['/usr/local/include', '/usr/include']
        if sys.platform == 'darwin':
            self.framework_path = ['/System/Library/Frameworks',
                                   '/Library/Frameworks']
        else:
            self.framework_path = []

        if gcc_search_path:
            self.add_gcc_search_path()
            self.add_cpp_search_path()

        self.lexer.filename = ''

        self.defines = {}
        self.namespace = PreprocessorNamespace()

    def define(self, name, value):
        self.defines[name] = value

    def add_gcc_search_path(self):
        from subprocess import Popen, PIPE
        path = Popen('gcc -print-file-name=include', 
                     shell=True, stdout=PIPE).communicate()[0].strip()
        if path:
            self.include_path.append(path)

    def add_cpp_search_path(self):
        from subprocess import Popen, PIPE
        try:
            open('test.h', 'a').close()
            output = Popen('cpp -v test.h', shell=True, stderr=PIPE).communicate()[1]
            import pdb; pdb.set_trace()
        finally:
            os.remove('test.h')
        if output:
            output = output.split('\n')
            while output and not '#include <...>' in output[0]:
                print('Skipping:', output[0])
                del output[0]
            if output:
                del output[0]  # Remove start line
                while output and not 'End of search list' in output[0]:
                    self.include_path.append(output[0].strip())
                    print('Adding:', output[0].strip())
                    del output[0]

    def parse(self, filename=None, data=None, namespace=None, debug=False): 
        self.output = []
        if not namespace:
            namespace = self.namespace
        for name, value in self.defines.items():
            namespace.define_object(name, (create_token('IDENTIFIER', value),))
        self.namespace = namespace
        self.imported_headers = set()
        self.condition_stack = [ExecutionState(True, True)]
        if filename:
            if not data:
                data = open(filename, 'r').read()
            self.lexer.input(data, filename)
        elif data:
            self.lexer.input(data, '<input>')

        return yacc.Parser.parse(self, debug=debug)

    def push_file(self, filename, data=None):
        print >> sys.stderr, filename
        if not data:
            data = open(filename).read()
        self.lexer.push_input(data, filename)

    def include(self, header):
        path = self.get_header_path(header)
        if path:
            self.push_file(path)
        else:
            print >> sys.stderr, '"%s" not found' % header # TODO

    def include_system(self, header):
        if header in self.system_headers:
            self.push_file(header, self.system_headers[header])
            return

        path = self.get_system_header_path(header)
        if path:
            self.push_file(path)
        else:
            print >> sys.stderr, '"%s" not found' % header # TODO

    def include_next(self, header, reference):
        # XXX doesn't go via get_system_header
        next = False
        for path in self.include_path:
            p = os.path.join(path, header)
            if os.path.exists(p):
                if next:
                    self.push_file(p)
                    return
                elif p == reference:
                    next = True
        print >> sys.stderr, '%s: cannot include_next from %s' % \
            (header, reference) # TODO

    def import_(self, header):
        path = self.get_header_path(header)
        if path:
            if path not in self.imported_headers:
                self.imported_headers.add(path)
                self.push_file(path)
        else:
            print >> sys.stderr, '"%s" not found' % header # TODO

    def import_system(self, header):
        if header in self.system_headers:
            if path not in self.imported_headers:
                self.imported_headers.add(path)
                self.push_file(header, self.system_headers[header])
            return
        path = self.get_system_header_path(header)
        if path:
            if path not in self.imported_headers:
                self.imported_headers.add(path)
                self.push_file(path)
        else:
            print >> sys.stderr, '"%s" not found' % header # TODO
 
    def get_header_path(self, header):
        p = os.path.join(os.path.dirname(self.lexer.filename), header)
        if os.path.exists(p):
            self.push_file(p)
            return p
        elif sys.platform == 'darwin':
            p = self.get_framework_header_path(header)
            if not p:
                p = self.get_system_header_path(header)
            return p

    def get_system_header_path(self, header):
        for path in self.include_path:
            p = os.path.join(path, header)
            if os.path.exists(p):
                return p
        if sys.platform == 'darwin':
            return self.get_framework_header_path(header)

    def get_framework_header_path(self, header):
        if '/' in header:
            # header is 'Framework/Framework.h' (e.g. OpenGL/OpenGL.h).
            framework, header = header.split('/', 1)

            paths = self.framework_path[:]
            # Add ancestor frameworks of current file
            localpath = ''
            for parent in self.lexer.filename.split('.framework/')[:-1]:
                localpath += parent + '.framework'
                paths.append(os.path.join(localpath, 'Frameworks'))
            for path in paths:
                p = os.path.join(path, '%s.framework' % framework, 
                                 'Headers', header)
                if os.path.exists(p):
                    return p

    def error(self, message, filename, line):
        print >> sys.stderr, '%s:%d #error %s' % (filename, line, message)
    
    def condition_if(self, result):
        self.condition_stack.append(
            ExecutionState(self.condition_stack[-1].enabled, result))

    def condition_elif(self, result):
        self.condition_stack[-1].enable(result)

    def condition_else(self):
        self.condition_stack[-1].enable(True)

    def condition_endif(self):
        self.condition_stack.pop()

    def enable_declaratives(self):
        return self.condition_stack[-1].enabled

    def enable_conditionals(self):
        return self.condition_stack[-1].enabled

    def enable_elif_conditionals(self):
        return self.condition_stack[-1].parent_enabled and \
               not self.condition_stack[-1].context_enabled

    def write(self, tokens):
        for t in tokens:
            if t.type == 'HEADER_NAME':
                # token was mis-parsed.  Do it again, without the '<', '>'.
                ta = create_token('<', '<')
                ta.filename = t.filename
                ta.lineno = t.lineno
                self.output.append(ta)

                l = lex.lex(cls=PreprocessorLexer)
                l.input(t.value, t.filename)
                l.lineno = t.lineno
                tb = l.token()
                while tb is not None:
                    if hasattr(tb, 'lexer'):
                        del tb.lexer
                    self.output.append(tb) 
                    tb = l.token()

                tc = create_token('>', '>')
                tc.filename = t.filename
                tc.lineno = t.lineno
                self.output.append(tc)

                continue

            if hasattr(t, 'lexer'):
                del t.lexer
            self.output.append(t)

    def get_memento(self):
        return (set(self.namespace.objects.keys()), 
                set(self.namespace.functions.keys()))

class ConstantExpressionParser(yacc.Parser):
    _const_grammar = ConstantExpressionGrammar

    def __init__(self, lexer, namespace):
        yacc.Parser.__init__(self)
        self.lexer = lexer
        self.namespace = namespace
        self._const_grammar.get_prototype().init_parser(self)

    def parse(self, debug=False):
        self.result = None
        try:
            yacc.Parser.parse(self, lexer=self.lexer, debug=debug)
        except ConstantExpressionParseException:
            # XXX warning here?
            pass
        return self.result

class StrictConstantExpressionParser(ConstantExpressionParser):
    _const_grammar = StrictConstantExpressionGrammar

class PreprocessorNamespace(EvaluationContext):
    def __init__(self, gcc_macros=True, 
                       stdc_macros=True,
                       workaround_macros=True):
        self.objects = {}
        self.functions = {}

        if stdc_macros:
            self.add_stdc_macros()
        
        if gcc_macros:
            self.add_gcc_macros()

        if workaround_macros:
            self.add_workaround_macros()

    def add_stdc_macros(self):
        '''Add macros defined in 6.10.8 except __FILE__ and __LINE__.

        This is potentially dangerous, as this preprocessor is not ISO
        compliant in many ways (the most obvious is the lack of # and ##
        operators).  It is required for Apple headers, however, which
        otherwise assume some truly bizarre syntax is ok.
        '''
        import time
        date = time.strftime('%b %d %Y') # XXX %d should have leading space
        t = time.strftime('%H:%M:S')
        self.define_object('__DATE__', 
                           (create_token('STRING_LITERAL', date),))
        self.define_object('__TIME__', 
                           (create_token('STRING_LITERAL', t),))
        self.define_object('__STDC__', 
                           (create_token('PP_NUMBER', '1'),))
        self.define_object('__STDC_HOSTED__', 
                           (create_token('PP_NUMBER', '1'),))
        self.define_object('__STDC_VERSION', 
                           (create_token('PP_NUMBER', '199901L'),))

    def add_gcc_macros(self):
        import platform
        import sys

        gcc_macros = ('__GLIBC_HAVE_LONG_LONG', '__GNUC__',)

        # Get these from `gcc -E -dD empty.c`
        machine_macros = {
            'x86_64': ('__amd64', '__amd64__', '__x86_64', '__x86_64__',
                       '__tune_k8__', '__MMX__', '__SSE__', '__SSE2__',
                       '__SSE_MATH__', '__k8', '__k8__'),
            'Power Macintosh': ('_ARCH_PPC', '__BIG_ENDIAN__', '_BIG_ENDIAN',
                                '__ppc__', '__POWERPC__'),
            # TODO everyone else.
        }.get(platform.machine(), ())
        platform_macros = {
            'linux': ('__gnu_linux__', '__linux', '__linux__', 'linux',
                       '__unix', '__unix__', 'unix'),
            'linux2': ('__gnu_linux__', '__linux', '__linux__', 'linux',
                       '__unix', '__unix__', 'unix'),
            'linux3': ('__gnu_linux__', '__linux', '__linux__', 'linux',
                       '__unix', '__unix__', 'unix'),
            'darwin': ('__MACH__', '__APPLE__', '__DYNAMIC__', '__APPLE_CC__'),
            'win32':  ('_WIN32',),
            # TODO everyone else
        }.get(sys.platform, ())

        tok1 = lex.LexToken()
        tok1.type = 'PP_NUMBER'
        tok1.value = '1'
        tok1.lineno = -1
        tok1.lexpos = -1
        
        for macro in machine_macros + platform_macros + gcc_macros:
            self.define_object(macro, (tok1,))

        self.define_object('inline', ())
        self.define_object('__inline', ())
        self.define_object('__inline__', ())
        self.define_object('__const', (create_token('IDENTIFIER', 'const'),))

    def add_workaround_macros(self):
        if sys.platform == 'darwin':
            self.define_object('CF_INLINE', ())

    def is_defined(self, name):
        return name in self.objects or name in self.functions

    def undef(self, name):
        if name in self.objects:
            del self.objects[name]

        if name in self.functions:
            del self.functions[name]

    def define_object(self, name, replacements):
        # TODO check not already existing in objects or functions
        for r in replacements:
            if hasattr(r, 'lexer'):
                del r.lexer
        self.objects[name] = replacements

    def define_function(self, name, params, replacements):
        # TODO check not already existing in objects or functions
        for r in replacements:
            if hasattr(r, 'lexer'):
                del r.lexer
        replacements = list(replacements)
        params = list(params)
        numargs = len(params)
        for i, t in enumerate(replacements):
            if hasattr(t, 'lexer'):
                del t.lexer
            if t.type == 'IDENTIFIER' and t.value in params:
                replacements[i] = params.index(t.value)
            elif t.type == 'IDENTIFIER' and t.value == '__VA_ARGS__' and \
                '...' in params:
                replacements[i] = len(params) - 1
                
        self.functions[name] = replacements, numargs

    def apply_macros(self, tokens, replacing=None):
        repl = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.type == 'IDENTIFIER' and token.value in self.objects:
                r = self.objects[token.value]
                if token.value != replacing and r:
                    repl += self.apply_macros(r, token.value)
            elif token.type == 'IDENTIFIER' and \
                 token.value in self.functions and \
                 len(tokens) - i > 2 and \
                 tokens[i+1].value == '(':

                r, numargs = self.functions[token.value][:]

                # build params list
                i += 2
                params = [[]]
                parens = 0  # balance parantheses within each arg
                while i < len(tokens):
                    if tokens[i].value == ',' and parens == 0 and \
                       len(params) < numargs:
                        params.append([])
                    elif tokens[i].value == ')' and parens == 0:
                        break
                    else:
                        if tokens[i].value == '(':
                            parens += 1
                        elif tokens[i].value == ')':
                            parens -= 1
                        params[-1].append(tokens[i])
                    i += 1

                if token.value != replacing and r:
                    newr = []
                    for t in r:
                        if type(t) == int:
                            newr += params[t]
                        else:
                            newr.append(t)
                    repl += self.apply_macros(newr, token.value)
            elif token.type == 'DEFINED':
                if len(tokens) - i > 3 and \
                   tokens[i + 1].type in ('(', 'LPAREN') and \
                   tokens[i + 2].type == 'IDENTIFIER' and \
                   tokens[i + 3].type == ')':
                    result = self.is_defined(tokens[i + 2].value)
                    i += 3
                elif len(tokens) - i > 1 and \
                    tokens[i + 1].type == 'IDENTIFIER':
                    result = self.is_defined(tokens[i + 1].value)
                    i += 1
                else:
                    # TODO
                    print >> sys.stderr, 'Invalid use of "defined"'
                    result = 0
                t = lex.LexToken()
                t.value = str(int(result))
                t.type = 'PP_NUMBER'
                t.lexpos = token.lexpos
                t.lineno = token.lineno
                repl.append(t)
            else:
                repl.append(token)
            i += 1
        return repl

    def copy(self):
        n = PreprocessorNamespace(gcc_macros=False, workaround_macros=False)
        n.functions = self.functions.copy()
        n.objects = self.objects.copy()
        return n

if __name__ == '__main__':
    filename = sys.argv[1]
    parser = PreprocessorParser()
    parser.parse(filename, debug=True)
    print ' '.join([str(t.value) for t in parser.output])
