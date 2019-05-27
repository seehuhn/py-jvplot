#! /usr/bin/env python3

"""A helper to keep the jvplot docstrings consistent."""

import argparse
import ast
import importlib
import os
import pkgutil
import re


_parser = argparse.ArgumentParser()
_parser.add_argument("-o", "--out", default="out",
                     help="directory to store output in")
_args = _parser.parse_args()


_DOCSTRING_RE = re.compile(r'(.*?\n *)""".*?"""\n', re.DOTALL)


def drop_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def stringify(node, lookup=None):
    """Turn the AST representation of dotted names (like a.b.c.) into
    string.

    """
    if lookup is None:
        lookup = {}

    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        name = node.id
        if name in lookup:
            name = lookup[name]
            parts.append(name)
    else:
        raise TypeError(f"node must be Name or Attribute (not f{type(node)})")
    return ".".join(reversed(parts))

def pretty(node, include_attributes=False, indent='  '):
    """Return a formatted dump of the tree in *node*.  This is mainly
    useful for debugging purposes.  The returned string will show the
    names and the values for fields.  Attributes such as line numbers
    and column offsets are not dumped by default.  If this is wanted,
    *include_attributes* can be set to True.

    """
    def _format(node, level=0):
        if isinstance(node, ast.AST):
            fields = [(a, _format(b, level)) for a, b in ast.iter_fields(node)]
            if include_attributes and node._attributes: #pylint: disable=W0212
                fields.extend([(a, _format(getattr(node, a), level))
                               for a in node._attributes]) #pylint: disable=W0212
            return ''.join([
                node.__class__.__name__,
                '(',
                ', '.join(('%s=%s' % field for field in fields)),
                ')'])
        if isinstance(node, list):
            lines = ['[']
            lines.extend((indent * (level + 2) + _format(x, level + 2) + ','
                          for x in node))
            if len(lines) > 1:
                lines.append(indent * (level + 1) + ']')
            else:
                lines[-1] += ']'
            return '\n'.join(lines)
        return repr(node)

    if not isinstance(node, (ast.AST, list)):
        raise TypeError('expected AST, got %r' % node.__class__.__name__)
    return _format(node)

def get_source(module_name):
    """Get the source code for a Python module."""
    spec = importlib.util.find_spec(module_name)
    return spec.loader.get_source(spec.name)

def load_ast(module_name):
    """Get the AST for a Python module."""
    spec = importlib.util.find_spec(module_name)
    source = spec.loader.get_source(spec.name)
    return ast.parse(source, spec.origin)

def submodules(package_name):
    """Yield all sub-modules of a Python package.

    The function returns a generator of all sub-module names, as
    strings.  Modules with names starting with "_" or "test_", or
    ending wiht "_test" are omitted from the result.

    """
    try:
        spec = importlib.util.find_spec(package_name)
    except ImportError:
        return
    yield package_name
    if not spec.submodule_search_locations:
        return
    for info in pkgutil.iter_modules(spec.submodule_search_locations):
        name = info.name
        if name.startswith("_") or name.startswith("test_") or name.endswith("_test"):
            continue
        sub = package_name + "." + name
        for subsub in submodules(sub):
            yield subsub

class FindClasses(ast.NodeVisitor):

    """A helper to find all class definitions in an AST tree.

    An AST tree can be analyzed by calling the `.visit()` method.
    After the traversal, results can be found in the `res` dictionary
    supplied to the constructor.

    """

    def __init__(self, module_name, res):
        """Create a new FindClasses object.

        Args:
            module_name: The name of the module being parsed.
            res (dict): A dictionary into which results will be stored
                while traversing the tree.  Keys are full parent class
                names, values are lists of child class names.  Classes
                with no parent class are ignored.

        """
        super().__init__()
        self.module_name = module_name
        self.imports = {}
        self.res = res

    def visit_Import(self, node): #pylint: disable=C0111
        for alias in node.names:
            global_name = alias.name
            local_name = alias.asname
            if not local_name:
                local_name = global_name
            self.imports[local_name] = global_name

    def visit_ImportFrom(self, node): #pylint: disable=C0111
        base = node.module
        if not base:
            base = ".".join(self.module_name.split(".")[:-1])
        for alias in node.names:
            global_name = alias.name
            local_name = alias.asname
            if not local_name:
                local_name = global_name
            self.imports[local_name] = base + "." + global_name

    def visit_ClassDef(self, node): #pylint: disable=C0111
        name = self.module_name + "." + node.name
        for base in node.bases:
            base_name = stringify(base, lookup=self.imports)
            if base_name not in self.res:
                self.res[base_name] = [name]
            else:
                self.res[base_name].append(name)

def find_descendants(root_class, package_name="jvplot"):
    """Find all (direct or indirect) subclasses of `root_class` in the
    submodules of Python package `package_name`.

    The function returns a set of full class names which derive from
    `root_class`.

    """

    children = {}
    for mod_name in submodules(package_name):
        tree = load_ast(mod_name)
        FindClasses(mod_name, children).visit(tree)

    todo = set([root_class])
    targets = set()
    while todo:
        name = todo.pop()
        if name in targets:
            continue
        targets.add(name)
        if name in children:
            todo.update(children[name])
    return targets


class StyleInfo:

    """Store information about the different drawing classes in jvplot.

    StyleInfo objects contain four fields:
        targets: set of full names of the classes to gather
            information about.  This is set in the constructur once
            and then never changed.
        methods: A map, where the keys are method names, and the
            values are 4-tuples stating (0) the full class name where
            the method is defined, (1) the names of all arguments, (2)
            a pair of line and column number where the method body
            starts and (3) the docstring of the method.
        uses: A map, where the keys are method names, and the values
            are lists of jvplot style parameter names used in the
            method.
        calls: A map, where the keys are method names, and the values
            are lists of drawing class methods called by this method.

    """

    def __init__(self, targets):
        """Create a new StyleInfo object.

        Args:
            targets (set of strings): full names of the classes to gather
                information about.
        """
        self.targets = targets
        self.methods = {}
        self.uses = {}
        self.calls = {}

    def modules(self):
        """Return a set of modules we have found methods in."""
        res = set()
        for class_name, _, _, _ in self.methods.values():
            module = ".".join(class_name.split(".")[:-1])
            res.add(module)
        return res

class FindStyleUsage(ast.NodeVisitor):

    """A helper to find all uses of jvplot style parameters in a method.

    An AST tree can be analyzed by calling the `.visit()` method.
    After the traversal, results can be found in the the `.uses` and
    `.calls` fields of the FindStyleUsage object.

    """

    def __init__(self):
        super().__init__()
        self.uses = set()
        self.calls = set()

    def visit_Call(self, node): #pylint: disable=C0111
        func = node.func

        if not (isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "self"):
            return
        if func.attr == "_get_param":
            param_name = node.args[0]
            assert isinstance(param_name, ast.Str), pretty(param_name)
            self.uses.add(param_name.s)
        else:
            self.calls.add(func.attr)

class FindMethods(ast.NodeVisitor):

    """A helper to find all methods in a class.

    This uses FindStyleUsage to find uses of jvplot style parameters
    inside the method definition.  Results are appended to the `info`
    object supplied to the constructor.

    """

    def __init__(self, info, class_name):
        """Create a new FindMethods object.

        Args:
            info (StyleInfo): A StyleInfo object to store the results
                in.
            class_name (string): The full name of the class being
                analyzed.

        """
        super().__init__()
        self.info = info
        self.class_name = class_name

    def visit_FunctionDef(self, node): #pylint: disable=C0111
        name = node.name
        if name == "__init__":
            name = self.class_name
        if name == "get_param" or name.startswith("__"):
            return

        if name == "close":
            # Method is defined on different sub-classes.  Since this
            # is the only overloaded name, it is easiest to skip this
            # method for now.
            return
        assert name not in self.info.methods, f"{name} is overloaded"

        args = node.args
        arg_names = [arg.arg for arg in args.args]
        if args.vararg:
            arg_names.append('*' + args.vararg.arg)
        arg_names.extend(arg.arg for arg in args.kwonlyargs)
        assert node.args.kwarg is None
        if arg_names and arg_names[0] == 'self':
            arg_names = arg_names[1:]

        docstring = ast.get_docstring(node, clean=True)

        self.info.methods[name] = (self.class_name,
                                   arg_names,
                                   (node.lineno, node.col_offset),
                                   docstring)

        usage = FindStyleUsage()
        usage.visit(node)
        self.info.uses[name] = usage.uses
        self.info.calls[name] = usage.calls

class FindClassMethods(ast.NodeVisitor):

    """A helper to find all jvplot drawing classes in a module.

    This uses FindMethods to find uses of jvplot style parameters
    inside the class' methods' definitions.  Results are written to the
    `info` object supplied to the constructor.

    """

    def __init__(self, info, module_name):
        """Create a new FindMethods object.

        Args:
            info (StyleInfo): A StyleInfo object to store the results
                in.
            module_name (string): The full name of the module being
                analyzed.

        """
        super().__init__()
        self.info = info
        self.module_name = module_name

    def visit_ClassDef(self, node): #pylint: disable=C0111
        name = self.module_name + "." + node.name
        if name in self.info.targets:
            FindMethods(self.info, name).visit(node)

def fix_args(old_args, real_args, module_file, lineno):
    arg_lines = {}
    cur_name = None
    cur_lines = []
    for l in old_args:
        l = l.rstrip()
        if not cur_lines and not l:
            continue
        if l.startswith("     ") or not l:
            cur_lines.append(l)
            continue
        if cur_lines:
            arg_lines[cur_name] = cur_lines
        cur_name = l.replace(":", " ").replace("(", " ").split()[0]
        cur_lines = [l]
    if cur_lines:
        arg_lines[cur_name] = cur_lines

    res = []
    used = set()
    for arg in real_args:
        used.add(arg)
        ll = arg_lines.get(arg)
        if ll:
            res.extend(ll)
        else:
            res.append(f"    {arg} ():")
    for arg, ll in arg_lines.items():
        if arg in used:
            continue
        print(f"{module_file}:{lineno}: non-existing argument {arg} in docstring")
        res.extend(ll)
    return res

def fix_docstring(orig, real_args, module_file, lineno):
    lines = orig.splitlines()
    out = []
    old_args = []
    in_doc = False
    has_args = False

    def write_args():
        nonlocal out
        out.append("Args:")
        out.extend(fix_args(old_args, real_args, module_file, lineno))

    for line in lines:
        line = line.rstrip()
        if in_doc:
            if not line or line[0].isspace():
                old_args.append(line)
                continue
            else:
                write_args()
                out.append("")
                in_doc = False
                has_args = True
        elif line.startswith("Args:"):
            assert not has_args, "docstring cannot have two Args sections"
            in_doc = True
            continue
        out.append(line)
    if in_doc or (real_args and not has_args):
        if not in_doc:
            while out and out[-1] == "":
                out = out[:-1]
            out.append("")
        write_args()
    return out

def _main():
    targets = find_descendants("jvplot.device.Device")
    info = StyleInfo(targets)

    modules = set()
    for target in targets:
        modules.add(".".join(target.split(".")[:-1]))
    for module in modules:
        tree = load_ast(module)
        FindClassMethods(info, module).visit(tree)

    try:
        os.makedirs(_args.out)
    except FileExistsError:
        pass
    for module in info.modules():
        print("processing", module, "...")
        module_file = drop_prefix(module, "jvplot.") + ".py"

        body = get_source(module)
        parts = []
        pos = 1

        def skip_to_line(l, drop=False):
            nonlocal body, pos
            m = re.match(r"(.*?\n){%d}" % (l-pos), body)
            b = m.end()
            if not drop:
                parts.append(body[:b])
            body = body[b:]
            pos = l

        for method, (class_name, args, (lineno, col), docstring) in info.methods.items():
            if not class_name.startswith(module + "."):
                continue
            if method.startswith("_"):
                continue
            if method != class_name:
                full_method = class_name + "." + method
            else:
                full_method = class_name + ".__init__"

            if not docstring:
                print(f"{module_file}:{lineno}: missing docstring for {full_method}")
                continue

            print(".", full_method)

            # remove the original docstring
            skip_to_line(lineno)
            m = _DOCSTRING_RE.match(body)
            skip_to_line(lineno + m.group(1).count('\n'))
            skip_to_line(lineno + m.group(0).count('\n'), drop=True)

            # add in the fixed docstring
            doc_lines = fix_docstring(docstring, args, module_file, lineno)
            pfx = " " * (col + 4)
            parts.append(pfx + '"""' + doc_lines[0] + "\n")
            parts.extend(pfx + l + "\n" for l in doc_lines[1:])
            parts.append("\n")
            parts.append(pfx + '"""\n')

        parts.append(body)

        out_name = os.path.join(_args.out, module_file)
        with open(out_name, "w") as fd:
            fd.write("".join(parts))
        print()

if __name__ == "__main__":
    _main()
