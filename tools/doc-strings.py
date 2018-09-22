#! /usr/bin/env python3

import argparse
import ast
import collections
import lib2to3
import re

parser = argparse.ArgumentParser()
parser.add_argument('fname', type=str,
                    help="the filename to analyse")
args = parser.parse_args()

with open(args.fname, "rt") as f:
    body = f.read()
    tree = ast.parse(body, args.fname)


docs = collections.OrderedDict()

def get_call_name(stmt):
    names = []
    while isinstance(stmt, ast.Attribute):
        names.append(stmt.attr)
        stmt = stmt.value
    if not isinstance(stmt, ast.Name):
        return []
    names.append(stmt.id)
    return list(reversed(names))

class FindMethods(ast.NodeVisitor):

    def visit_FunctionDef(self, node):
        name = node.name
        # if name.startswith("__"):
        #     return
        argnames = [arg.arg for arg in node.args.args]
        argnames.extend(arg.arg for arg in node.args.kwonlyargs)
        assert node.args.kwarg is None
        if argnames[0] != 'self':
            return
        argnames = argnames[1:]
        if not name.startswith("__"):
            docstring = ast.get_docstring(node)
            docs[name] = (node.lineno, argnames, docstring)

        print("**", name, "**")
        for stmt in ast.walk(node):
            if not isinstance(stmt, ast.Call):
                continue
            names = get_call_name(stmt.func)
            if not names or names[0] != 'self':
                continue
            if name != "get_param" and names[1].endswith('get_param'):
                print("uses '" + stmt.args[0].s + "'")
            else:
                print("calls", ".".join(names))
        print("")

class FindClasses(ast.NodeVisitor):

    def visit_ClassDef(self, node):
        FindMethods().visit(node)

FindClasses().visit(tree)

def indent(line):
    ind = 0
    while line[ind] == ' ':
        ind += 1
    return ind

docstrings = []
for name, (lineno, args, doc) in docs.items():
    changed = False
    if not doc:
        doc = ""
    doc = doc.splitlines()
    out = []
    in_doc = False
    has_args = False
    doc_indent = 0
    for line in doc:
        line = line.rstrip()
        if not line:
            out.append(line)
            continue
        if line.startswith("Args:"):
            in_doc = True
            has_args = True
        elif in_doc:
            ind = indent(line)
            if not doc_indent:
                doc_indent = ind
                assert doc_indent > 0
            if ind > doc_indent:
                out.append(line)
                continue
            if ind < doc_indent and args:
                in_doc = False
                target = None
            else:
                target = line.split()[0]
                if target[-1] == ":":
                    target = target[:-1]
            while target in args:
                arg = args.pop(0)
                if arg != target:
                    out.append(" "*doc_indent + arg + " (): ")
        out.append(line)
    if not has_args:
        out.append("")
        out.append("Args:")
    if not doc_indent:
        doc_indent = 4
    for arg in args:
        out.append(" "*doc_indent + arg + " (): ")
    docstrings.append((name, lineno, out))

parts = []
pos = 0
for name, lineno, docstring in docstrings:
    lineno -= 1
    m = re.match(r"(.*?\n){%d}" % (lineno-pos), body)
    b = m.end()
    parts.append(body[:b])
    body = body[b:]
    pos = lineno
    indent = len(m.group(1)) + 4

    m = re.match(r"( *)def " + name + r"\([^)]*\):\n", body)
    b = m.end()
    parts.append(body[:b])
    body = body[b:]
    pos += m.group(0).count('\n')

    m = re.match(r'( *)""".*?"""\n', body, re.DOTALL)
    if m:
        b = m.end()
        body = body[b:]
        pos += m.group(0).count('\n')
        indent = len(m.group(1))
    pfx = " " * indent
    parts.append(pfx + '"""' + docstring[0] + "\n")
    parts.extend(pfx + l + "\n" for l in docstring[1:])
    parts.append("\n")
    parts.append(pfx + '"""\n')
parts.append(body)

print("".join(parts))
