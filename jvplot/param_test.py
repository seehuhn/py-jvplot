#! /usr/bin/env python3

import numpy as np

import nose.tools

from . import param

def test_update():
    style = param.update({})
    assert(style['bg_col'] == 'transparent')

    style = param.update({}, param.ROOT)
    assert(style['bg_col'] == 'white')
