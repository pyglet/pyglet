wraptypes
=========

wraptypes is a general utility for creating ctypes wrappers from C header
files.  The front-end is ``tools/wraptypes/wrap.py``, for usage::

    python tools/wraptypes/wrap.py -h

There are three components to wraptypes:

preprocessor.py
    Interprets preprocessor declarations and converts the source header files
    into a list of tokens.
cparser.py
    Parses the preprocessed tokens for type and function declarations and
    calls ``handle_`` methods on the class CParser in a similar manner to a
    SAX parser.
ctypesparser.py
    Interprets C declarations and types from CParser and creates corresponding
    ctypes declarations, calling ``handle_`` methods on the class
    CtypesParser.

.. image: wraptypes-class.svg

The front-end ``wrap.py`` provides a simple subclass of ``CtypesParser``,
``CtypesWrapper``, which writes the ctypes declarations found to a file in a
format that can be imported as a module.

Parser Modifications
--------------------

The parsers are built upon a modified version of `PLY`_, a Python
implementation of lex and yacc. The modified source is included in
the ``wraptypes`` directory.  The modifications are:

* Grammar is abstracted out of Parser, so multiple grammars can easily be
  defined in the same module.
* Tokens and symbols keep track of their filename as well as line number.
* Lexer state can be pushed onto a stack.

The first time the parsers are run (or after they are modified), PLY creates
``pptab.py`` and ``parsetab.py`` in the current directory.  These are
the generated state machines, which can take a few seconds to generate.
The file ``parser.out`` is created if debugging is enabled, and contains the
parser description (of the last parser that was generated), which is essential
for debugging.

.. _PLY: http://www.dabeaz.com/ply/

Preprocessor
------------

The grammar and parser are defined in ``preprocessor.py``.

There is only one lexer state.  Each token has a type which is a string (e.g.
``'CHARACTER_CONSTANT'``) and a value.  Token values, when read directly from
the source file are only ever strings.  When tokens are written to the output
list they sometimes have tuple values (for example, a ``PP_DEFINE`` token on
output).

Two lexer classes are defined: ``PreprocessorLexer``, which reads a stack of
files (actually strings) as input, and ``TokenListLexer``, which reads from a
list of already-parsed tokens (used for parsing expressions).

The preprocessing entry-point is the ``PreprocessorParser`` class.  This
creates a ``PreprocessorLexer`` and its grammar during construction.  The
system include path includes the GCC search path by default but can be
modified by altering the ``include_path`` and ``framework_path`` lists.  The
``system_headers`` dict allows header files to be implied on the search path
that don't exist.  For example, by setting::

    system_headers['stdlib.h'] = '''#ifndef STDLIB_H
    #define STDLIB_H

    /* ... */
    #endif
    '''

you can insert your own custom header in place of the one on the filesystem.
This is useful when parsing headers from network locations.

Parsing begins when ``parse`` is called.  Specify one or both of a filename
and a string of data.  If ``debug`` kwarg is True, syntax errors dump the
parser state instead of just the line number where they occurred.

The production rules specify the actions; these are implemented in
``PreprocessorGrammar``.  The actions call methods on ``PreprocessorParser``,
such as:

* ``include(self, header)``, to push another file onto the lexer.
* ``include_system(self, header)``, to search the system path for a file to
  push onto the lexer
* ``error(self, message, filename, line)``, to signal a parse error.  Not
  all syntax errors get this far, due to limitations in the parser.  A parse
  error at EOF will just print to stderr.
* ``write(self, tokens)``, to write tokens to the output list.  This is
  the default action when no preprocessing declaratives are being parsed.

The parser has a stack of ``ExecutionState``, which specifies whether the
current tokens being parsed are ignored or not (tokens are ignored in an
``#if`` that evaluates to 0).  This is a little more complicated than just a
boolean flag:  the parser must also ignore #elif conditions that can have no
effect.  The ``enable_declaratives`` and ``enable_elif_conditionals`` return
True if the top-most ``ExecutionState`` allows declaratives and ``#elif``
conditionals to be parsed, respecitively.  The execution state stack is
modified with the ``condition_*`` methods.

``PreprocessorParser`` has a ``PreprocessorNamespace`` which keeps track of
the currently defined macros.  You can create and specify your own namespace,
or use one that is created by default.  The default namespace includes GCC
platform macros needed for parsing system headers, and some of the STDC
macros.

Macros are expanded when tokens are written to the output list, and when
conditional expressions are parsed.
``PreprocessorNamespace.apply_macros(tokens)`` takes care of this, replacing
function parameters, variable arguments, macro objects and (mostly) avoiding
infinite recursion.  It does not yet handle the ``#`` and ``##`` operators,
which are needed to parse the Windows system headers.

The process for evaluating a conditional (``#if`` or ``#elif``) is:

1. Tokens between ``PP_IF`` or ``PP_ELIF`` and ``NEWLINE`` are expanded
   by ``apply_macros``.
2. The resulting list of tokens is used to construct a ``TokenListLexer``.
3. This lexer is used as input to a ``ConstantExpressionParser``.  This parser
   uses the ``ConstantExpressionGrammar``, which builds up an AST of
   ``ExpressionNode`` objects.
4. ``parse`` is called on the ``ConstantExpressionParser``, which returns the
   resulting top-level ``ExpressionNode``, or ``None`` if there was a syntax
   error.
5. The ``evaluate`` method of the ``ExpressionNode`` is called with the
   preprocessor's namespace as the evaluation context.  This allows the
   expression nodes to resolve ``defined`` operators.
6. The result of ``evaluate`` is always an int; non-zero values are treated as
   True.

Because pyglet requires special knowledge of the preprocessor declaratives
that were encountered in the source, these are encoded as pseudo-tokens within
the output token list.  For example, after a ``#ifndef`` is evaluated, it
is written to the token list as a ``PP_IFNDEF`` token.

``#define`` is handled specially.  After applying it to the namespace, it is
parsed as an expression immediately.  This is allowed (and often expected) to
fail.  If it does not fail, a ``PP_DEFINE_CONSTANT`` token is created, and the
value is the result of evaluatin the expression.  Otherwise, a ``PP_DEFINE``
token is created, and the value is the string concatenation of the tokens
defined.  Special handling of parseable expressions makes it simple to later
parse constants defined as, for example::

    #define RED_SHIFT 8
    #define RED_MASK (0x0f << RED_SHIFT)

The preprocessor can be tested/debugged by running ``preprocessor.py``
stand-alone with a header file as the sole argument.  The resulting token list
will be written to stdout.

CParser
-------

The lexer for ``CParser``, ``CLexer``, takes as input a list of tokens output
from the preprocessor.  The special preprocessor tokens such as ``PP_DEFINE``
are intercepted here and handled immediately; hence they can appear anywhere
in the source header file without causing problems with the parser.  At this
point ``IDENTIFIER`` tokens which are found to be the name of a defined type
(the set of defined types is updated continuously during parsing) are
converted to ``TYPE_NAME`` tokens.

The entry-point to parsing C source is the ``CParser`` class.  This creates a
preprocessor in its constructor, and defines some default types such as
``wchar_t`` and ``__int64_t``.  These can be disabled with kwargs.

Preprocessing can be quite time-consuming, especially on OS X where thousands
of ``#include`` declaratives are processed when Carbon is parsed.  To minimise
the time required to parse similar (or the same, while debugging) header
files, the token list from preprocessing is cached and reused where possible.

This is handled by ``CPreprocessorParser``, which overrides ``push_file`` to
check with ``CParser`` if the desired file is cached.  The cache is checked
against the file's modification timestamp as well as a "memento" that
describes the currently defined tokens.  This is intended to avoid using a
cached file that would otherwise be parsed differently due to the defined
macros.  It is by no means perfect; for example, it won't pick up on a macro
that has been defined differently.  It seems to work well enough for the
header files pyglet requires.

The header cache is saved and loaded automatically in the working directory
as ``.header.cache``.  The cache should be deleted if you make changes to the
preprocessor, or are experiencing cache errors (these are usually accompanied
by a "what-the?" exclamation from the user).

The actions in the grammar construct parts of a "C object model" and call
methods on ``CParser``.  The C object model is not at all complete, containing
only what pyglet (and any other ctypes-wrapping application) requires.  The
classes in the object model are:

Declaration
    A single declaration occuring outside of a function body.  This includes
    type declarations, function declarations and variable declarations.  The
    attributes are ``declarator`` (see below), ``type`` (a Type object) and
    ``storage`` (for example, 'typedef', 'const', 'static', 'extern', etc).
Declarator
    A declarator is a thing being declared.  Declarators have an
    ``identifier`` (the name of it, None if the declarator is abstract, as in
    some function parameter declarations), an optional ``initializer``
    (currently ignored), an optional linked-list of ``array`` (giving the
    dimensions of the array) and an optional list of ``parameters`` (if the
    declarator is a function).
Pointer
    This is a type of declarator that is dereferenced via ``pointer`` to
    another declarator.
Array
    Array has size (an int, its dimension, or None if unsized) and a pointer
    ``array`` to the next array dimension, if any.
Parameter
    A function parameter consisting of a ``type`` (Type object), ``storage``
    and ``declarator``.
Type
    Type has a list of ``qualifiers`` (e.g. 'const', 'volatile', etc) and
    ``specifiers`` (the meaty bit).
TypeSpecifier
    A base TypeSpecifier is just a string, such as ``'int'`` or ``'Foo'`` or
    ``'unsigned'``.  Note that types can have multiple TypeSpecifiers; not
    all combinations are valid.
StructTypeSpecifier
    This is the specifier for a struct or union (if ``is_union`` is True)
    type.  ``tag`` gives the optional ``foo`` in ``struct foo`` and
    ``declarations`` is the meat (an empty list for an opaque or unspecified
    struct).
EnumSpecifier
    This is the specifier for an enum type.  ``tag`` gives the optional
    ``foo`` in ``enum foo`` and ``enumerators`` is the list of Enumerator
    objects (an empty list for an unspecified enum).
Enumerator
    Enumerators exist only within EnumSpecifier.  Contains ``name`` and
    ``expression``, an ExpressionNode object.

The ``ExpressionNode`` object hierarchy is similar to that used in the
preprocessor, but more fully-featured, and using a different
``EvaluationContext`` which can evaluate identifiers and the ``sizeof``
operator (currently it actually just returns 0 for both).

Methods are called on CParser as declarations and preprocessor declaratives
are parsed.  The are mostly self explanatory.  For example:

handle_ifndef(self, name, filename, lineno)
    An ``#ifndef`` was encountered testing the macro ``name`` in file
    ``filename`` at line ``lineno``.
handle_declaration(self, declaration, filename, lineno)
    ``declaration`` is an instance of Declaration.

These methods should be overridden by a subclass to provide functionality.
The ``DebugCParser`` does this and prints out the arguments to each
``handle_`` method.

The ``CParser`` can be tested in isolation by running it stand-alone with the
filename of a header as the sole argument.  A ``DebugCParser`` will be
constructed and used to parse the header.

CtypesParser
------------

``CtypesParser`` is implemented in ``ctypesparser.py``.  It is a subclass of
``CParser`` and implements the ``handle_`` methods to provide a more
ctypes-friendly interpretation of the declarations.

To use, subclass and override the methods:

handle_ctypes_constant(self, name, value, filename, lineno)
    An integer or float constant (in a ``#define``).
handle_ctypes_type_definition(self, name, ctype, filename, lineno)
    A ``typedef`` declaration.  See below for type of ``ctype``.
handle_ctypes_function(self, name, restype, argtypes, filename, lineno)
    A function declaration with the given return type and argument list.
handle_ctypes_variable(self, name, ctype, filename, lineno)
    Any other non-``static`` declaration.

Types are represented by instances of ``CtypesType``.  This is more easily
manipulated than a "real" ctypes type.  There are subclasses for
``CtypesPointer``, ``CtypesArray``, ``CtypesFunction``, and so on; see the
module for details.

Each ``CtypesType`` class implements the ``visit`` method, which can be used,
Visitor pattern style, to traverse the type hierarchy.  Call the ``visit``
method of any type with an implementation of ``CtypesTypeVisitor``: all
pointers, array bases, function parameters and return types are traversed
automatically (struct members are not, however).

This is useful when writing the contents of a struct or enum.  Before writing
a type declaration for a struct type (which would consist only of the struct's
tag), ``visit`` the type and handle the ``visit_struct`` method on the visitor
to print out the struct's members first.  Similarly for enums.

``ctypesparser.py`` can not be run stand-alone.  ``wrap.py`` provides a
straight-forward implementation that writes a module of ctypes wrappers.  It
can filter the output based on the originating filename.  See the module
docstring for usage and extension details.
