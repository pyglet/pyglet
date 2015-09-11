# -*- coding: utf-8 -*-
"""
    sphinx.ext.autosummary.generate
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Usable as a library or script to generate automatic RST source files for
    items referred to in autosummary:: directives.

    Each generated RST file contains a single auto*:: directive which
    extracts the docstring of the referred item.

    Example Makefile rule::

       generate:
               sphinx-autogen -o source/generated source/*.rst

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
import re
import sys
import pydoc
import optparse
import codecs
import inspect

from jinja2 import FileSystemLoader, TemplateNotFound
from jinja2.sandbox import SandboxedEnvironment

from sphinx import package_dir
from ..autosummary import import_by_name, get_documenter
from sphinx.jinja2glue import BuiltinTemplateLoader
from sphinx.util.osutil import ensuredir
from sphinx.util.inspect import safe_getattr
from sphinx.pycode import ModuleAnalyzer

# Add documenters to AutoDirective registry
from sphinx.ext.autodoc import add_documenter, \
    ModuleDocumenter, ClassDocumenter, ExceptionDocumenter, DataDocumenter, \
    FunctionDocumenter, MethodDocumenter, AttributeDocumenter, \
    InstanceAttributeDocumenter
add_documenter(ModuleDocumenter)
add_documenter(ClassDocumenter)
add_documenter(ExceptionDocumenter)
add_documenter(DataDocumenter)
add_documenter(FunctionDocumenter)
add_documenter(MethodDocumenter)
add_documenter(AttributeDocumenter)
add_documenter(InstanceAttributeDocumenter)


def main(argv=sys.argv):
    usage = """%prog [OPTIONS] SOURCEFILE ..."""
    p = optparse.OptionParser(usage.strip())
    p.add_option("-o", "--output-dir", action="store", type="string",
                 dest="output_dir", default=None,
                 help="Directory to place all output in")
    p.add_option("-s", "--suffix", action="store", type="string",
                 dest="suffix", default="rst",
                 help="Default suffix for files (default: %default)")
    p.add_option("-t", "--templates", action="store", type="string",
                 dest="templates", default=None,
                 help="Custom template directory (default: %default)")
    options, args = p.parse_args(argv[1:])

    if len(args) < 1:
        p.error('no input files given')

    generate_autosummary_docs(args, options.output_dir,
                              "." + options.suffix,
                              template_dir=options.templates)


def _simple_info(msg):
    print(msg)


def _simple_warn(msg):
    print('WARNING: ' + msg, file=sys.stderr)


        
    
# -- Generating output ---------------------------------------------------------

def generate_autosummary_docs(sources, output_dir=None, suffix='.rst',
                              warn=_simple_warn, info=_simple_info,
                              base_path=None, builder=None, template_dir=None):

    showed_sources = list(sorted(sources))
    if len(showed_sources) > 20:
        showed_sources = showed_sources[:10] + ['...'] + showed_sources[-10:]
    info('[autosummary] generating autosummary for: %s' %
         ', '.join(showed_sources))

    if output_dir:
        info('[autosummary] writing to %s' % output_dir)

    if base_path is not None:
        sources = [os.path.join(base_path, filename) for filename in sources]

    # create our own templating environment
    template_dirs = [os.path.join(package_dir, 'ext',
                                  'autosummary', 'templates')]
    if builder is not None:
        # allow the user to override the templates
        template_loader = BuiltinTemplateLoader()
        template_loader.init(builder, dirs=template_dirs)
    else:
        if template_dir:
            template_dirs.insert(0, template_dir)
        template_loader = FileSystemLoader(template_dirs)
    template_env = SandboxedEnvironment(loader=template_loader)

    # read
    items = find_autosummary_in_files(sources)

    # keep track of new files
    new_files = []

    # write
    for name, path, template_name in sorted(set(items), key=str):
        if path is None:
            # The corresponding autosummary:: directive did not have
            # a :toctree: option
            continue

        path = output_dir or os.path.abspath(path)
        ensuredir(path)

        try:
            name, obj, parent, mod_name = import_by_name(name)
        except ImportError as e:
            warn('[autosummary] failed to import %r: %s' % (name, e))
            continue

        # skip base modules
        if name.endswith(".base"):
            continue
            
        fn = os.path.join(path, name + suffix)

        # skip it if it exists
        if os.path.isfile(fn):
            continue

        new_files.append(fn)

        with open(fn, 'w') as f:
            doc = get_documenter(obj, parent)

            if template_name is not None:
                template = template_env.get_template(template_name)
            else:
                try:
                    template = template_env.get_template('autosummary/%s.rst'
                                                         % doc.objtype)
                except TemplateNotFound:
                    template = template_env.get_template('autosummary/base.rst')

            def exclude_member(obj, name):
                if sys.skip_member(name, obj): 
                    return True
                
                live = getattr(obj, name)

                if inspect.isbuiltin(live): 
                    return True

                real_module = inspect.getmodule(live)
                if real_module is not None:
                    if real_module.__name__ in ["ctypes", 
                                                "unittest"]: 
                        return True
                    
                c = getattr(obj, name)
                if inspect.isclass(c) or inspect.isfunction(c):
                    if (c.__module__!=obj.__name__+".base" and
                        c.__module__!=obj.__name__):
                        return True
                return False
                
            def get_members(obj, typ, include_public=[]):
                items = []
                for name in dir(obj):
                    # skip_member
                    if exclude_member(obj, name): 
                        continue
                    try:
                        documenter = get_documenter(safe_getattr(obj, name),
                                                    obj)
                    except AttributeError:
                        continue
                    if documenter.objtype == typ:
                        items.append(name)
                    elif typ=='function' and documenter.objtype=='boundmethod':
                        items.append(name)
                public = [x for x in items
                          if x in include_public or not x.startswith('_')]
                return public, items

            def def_members(obj, typ, include_public=[]):
                items = []
                try:
                    obj_dict = safe_getattr(obj, '__dict__')
                except AttributeError:
                    return []
                for name in sorted(obj_dict.keys()):
                    if exclude_member(obj, name): 
                        continue
                    try:
                        documenter = get_documenter(safe_getattr(obj, name), obj)
                    except AttributeError:
                        continue
                    if documenter.objtype == typ:
                        items.append(name)
                public = [x for x in items
                          if x in include_public or not x.startswith('_')]
                return public

            def get_iattributes(obj):
                items = []
                name = obj.__name__
                obj_attr = dir(obj)
                analyzer = ModuleAnalyzer.for_module(obj.__module__)
                attr_docs = analyzer.find_attr_docs()
                for pair, doc in attr_docs.items():
                    if name!=pair[0]:
                        continue
                    if not pair[1] in obj_attr:
                        items.append({"name":pair[1],
                                      "doc":'\n   '.join(doc)})
                items.sort(key=lambda d: d["name"]) 
                return items

            ns = {}

            if doc.objtype == 'module':
                ns['all_members'] = dir(obj)

                ns['classes'], ns['all_classes'] = \
                    get_members(obj, 'class')
                ns['functions'], ns['all_functions'] = \
                                   get_members(obj, 'function')
                ns['exceptions'], ns['all_exceptions'] = \
                    get_members(obj, 'exception')
                ns['data'], ns['all_data'] = \
                                   get_members(obj, 'data')
                documented = ns['classes']+ns['functions'] +ns['exceptions']+ns['data']

                if obj.__name__ in sys.all_submodules:
                    ns['submodules'] = sys.all_submodules[obj.__name__]
                    # Hide base submodule
                    if "base" in ns['submodules']:
                        ns['submodules'].remove("base")
                    documented += ns['submodules']

                ns['members'] = ns['all_members']
                try:
                    obj_dict = safe_getattr(obj, '__dict__')
                except AttributeError:
                    obj_dict = []

                public = [x for x in obj_dict if not x.startswith('_')]
                for item in documented:
                    if item in public:
                        public.remove(item)

                public.sort()
                ns['members'] = public
                ns['constants'] = [x for x in public
                                   #if not sys.skip_member(x, obj)]
                                   if not exclude_member(obj, x)]

            elif doc.objtype == 'class':
                ns['members'] = dir(obj)
                ns['events'], ns['all_events'] = \
                                 get_members(obj, 'event')
                ns['methods'], ns['all_methods'] = \
                    get_members(obj, 'method', ['__init__'])
                ns['attributes'], ns['all_attributes'] = \
                    get_members(obj, 'attribute')
                # Add instance attributes
                ns['iattributes'] = get_iattributes(obj)
                ns['def_events'] = def_members(obj, 'event')
                ns['def_methods'] = def_members(obj, 'method')
                ns['def_attributes'] = def_members(obj, 'attribute')

                # Constructor method special case
                if '__init__' in ns['methods']:
                    ns['methods'].remove('__init__')
                    if '__init__' in ns['def_methods']:
                        ns['def_methods'].remove('__init__')
                    ns['constructor']=['__init__']
                else:
                    ns['constructor']=[]

                ns['inherited'] = []
                for t in ['events', 'methods', 'attributes']:
                    key = 'inh_' + t
                    ns[key]=[]
                    for item in ns[t]:
                        if not item in ns['def_' + t]:
                            ns['inherited'].append(item)
                            ns[key].append(item)


            parts = name.split('.')
            if doc.objtype in ('method', 'attribute'):
                mod_name = '.'.join(parts[:-2])
                cls_name = parts[-2]
                obj_name = '.'.join(parts[-2:])
                ns['class'] = cls_name
            else:
                mod_name, obj_name = '.'.join(parts[:-1]), parts[-1]

            ns['fullname'] = name
            ns['module'] = mod_name
            ns['objname'] = obj_name
            ns['name'] = parts[-1]

            ns['objtype'] = doc.objtype
            ns['underline'] = len(name) * '='

            rendered = template.render(**ns)
            f.write(rendered)

    # descend recursively to new files
    if new_files:
        generate_autosummary_docs(new_files, output_dir=output_dir,
                                  suffix=suffix, warn=warn, info=info,
                                  base_path=base_path, builder=builder,
                                  template_dir=template_dir)


# -- Finding documented entries in files ---------------------------------------

def find_autosummary_in_files(filenames):
    """Find out what items are documented in source/*.rst.

    See `find_autosummary_in_lines`.
    """
    documented = []
    for filename in filenames:
        with codecs.open(filename, 'r', encoding='utf-8',
                         errors='ignore') as f:
            lines = f.read().splitlines()
            documented.extend(find_autosummary_in_lines(lines,
                                                        filename=filename))
    return documented


def find_autosummary_in_docstring(name, module=None, filename=None):
    """Find out what items are documented in the given object's docstring.

    See `find_autosummary_in_lines`.
    """
    try:
        real_name, obj, parent, modname = import_by_name(name)
        lines = pydoc.getdoc(obj).splitlines()
        return find_autosummary_in_lines(lines, module=name, filename=filename)
    except AttributeError:
        pass
    except ImportError as e:
        print("Failed to import '%s': %s" % (name, e))
    except SystemExit as e:
        print("Failed to import '%s'; the module executes module level "
              "statement and it might call sys.exit()." % name)
    return []


def find_autosummary_in_lines(lines, module=None, filename=None):
    """Find out what items appear in autosummary:: directives in the
    given lines.

    Returns a list of (name, toctree, template) where *name* is a name
    of an object and *toctree* the :toctree: path of the corresponding
    autosummary directive (relative to the root of the file name), and
    *template* the value of the :template: option. *toctree* and
    *template* ``None`` if the directive does not have the
    corresponding options set.
    """
    autosummary_re = re.compile(r'^(\s*)\.\.\s+autosummary::\s*')
    automodule_re = re.compile(
        r'^\s*\.\.\s+automodule::\s*([A-Za-z0-9_.]+)\s*$')
    module_re = re.compile(
        r'^\s*\.\.\s+(current)?module::\s*([a-zA-Z0-9_.]+)\s*$')
    autosummary_item_re = re.compile(r'^\s+(~?[_a-zA-Z][a-zA-Z0-9_.]*)\s*.*?')
    toctree_arg_re = re.compile(r'^\s+:toctree:\s*(.*?)\s*$')
    template_arg_re = re.compile(r'^\s+:template:\s*(.*?)\s*$')

    documented = []

    toctree = None
    template = None
    current_module = module
    in_autosummary = False
    base_indent = ""

    for line in lines:
        if in_autosummary:
            m = toctree_arg_re.match(line)
            if m:
                toctree = m.group(1)
                if filename:
                    toctree = os.path.join(os.path.dirname(filename),
                                           toctree)
                continue

            m = template_arg_re.match(line)
            if m:
                template = m.group(1).strip()
                continue

            if line.strip().startswith(':'):
                continue  # skip options

            m = autosummary_item_re.match(line)
            if m:
                name = m.group(1).strip()
                if name.startswith('~'):
                    name = name[1:]
                if current_module and \
                   not name.startswith(current_module + '.'):
                    name = "%s.%s" % (current_module, name)
                documented.append((name, toctree, template))
                continue

            if not line.strip() or line.startswith(base_indent + " "):
                continue

            in_autosummary = False

        m = autosummary_re.match(line)
        if m:
            in_autosummary = True
            base_indent = m.group(1)
            toctree = None
            template = None
            continue

        m = automodule_re.search(line)
        if m:
            current_module = m.group(1).strip()
            # recurse into the automodule docstring
            documented.extend(find_autosummary_in_docstring(
                current_module, filename=filename))
            continue

        m = module_re.match(line)
        if m:
            current_module = m.group(2)
            continue

    return documented


if __name__ == '__main__':
    main()
