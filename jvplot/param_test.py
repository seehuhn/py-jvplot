#! /usr/bin/env python3

from . import param

def test_update():
    style = param.update({}, param.ROOT)
    assert style['bg_col'] == 'white'
