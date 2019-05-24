#! /usr/bin/env python3

import astroid

def _main():
    manager = astroid.manager.AstroidManager()
    ast = manager.ast_from_module_name("jvplot.canvas")
    for node in ast.body:
        if not isinstance(node, astroid.nodes.ClassDef):
            continue
        if node.name != "Canvas":
            continue
        canvas = node
        break
    else:
        raise NotImplementedError("Canvas class not found")

    for method in canvas.body:
        if not isinstance(method, astroid.nodes.FunctionDef):
            continue
        if method.name.startswith("_"):
            continue
        print(method.as_string())

if __name__ == "__main__":
    _main()
