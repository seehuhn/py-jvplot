#! /usr/bin/env python3

import numpy as np

import nose.tools

from . import canvas
from . import color
from . import errors
from . import param
from . import plot
from . import util


def test_close_hooks():
    pl = plot.Plot('/dev/null', 3, 3)
    ax = pl.viewport([0, 0, pl.width, pl.height], (0, 1), (0, 1))
    seen = False
    def hook():
        nonlocal seen
        seen = True
    ax._on_close.append(hook)
    pl.close()
    assert seen

def test_canvas_param():
    res = 100
    lw = '17pt'
    c1 = canvas.Canvas(None, [0, 0, 200, 400], res=res, parent=None,
                       style={'padding': '0pt',
                              'axis_margin_left': '10%',
                              'axis_margin_top': '20%',
                              'axis_margin_bottom': '$axis_margin_right',
                              'lw': lw})

    # parameter type 'width'
    key = 'axis_margin_left'
    val = c1.get_param(key)
    nose.tools.assert_almost_equal(val, 0.1*200)

    # parameter type 'height'
    key = 'axis_margin_top'
    val = c1.get_param(key)
    nose.tools.assert_almost_equal(val, 0.2*400)

    # parameter type 'dim'
    key = 'font_size'
    val = c1.get_param(key)
    assert val == util.convert_dim(param.DEFAULT[key][1], res)

    # parameter type 'col'
    key = 'line_col'
    val = c1.get_param(key)
    assert val == color.get(param.DEFAULT[key][1])

    # parameter type 'bool'
    key = 'plot_point_separate'
    val = c1.get_param(key)
    assert val == param.DEFAULT[key][1]

    # variables
    key = 'plot_lw'             # default value is '$lw'
    val = c1.get_param(key)
    nose.tools.assert_almost_equal(val, util.convert_dim(lw, res))

    # invalid parameter names
    with nose.tools.assert_raises(errors.InvalidParameterName):
        # mis-spelled 'font_size'
        canvas.Canvas(None, [50, 100, 100, 200], res=res, parent=c1,
                      style={'font.size': '10px'})
    with nose.tools.assert_raises(errors.InvalidParameterName):
        # mis-spelled 'font_size'
        c1.get_param('font.size')
    with nose.tools.assert_raises(errors.InvalidParameterName):
        # mis-spelled 'font_size'
        c1.get_param('font_size', style={'font.size': '10px'})

def test_data_range():
    with nose.tools.assert_raises(ValueError):
        canvas.data_range()

    a, b = canvas.data_range(1)
    assert a == 1 and b == 1

    a, b = canvas.data_range(3, 1, 4, 1, 5)
    assert a == 1 and b == 5

    a, b = canvas.data_range([3, 1, 4, 1, 5])
    assert a == 1 and b == 5

    a, b = canvas.data_range([1, (2, 3)],
                             [4, 5, 6],
                             np.arange(7, 10))
    assert a == 1 and b == 9

    a, b = canvas.data_range(np.inf, -np.inf, 2, np.nan)
    assert a == 2 and b == 2

    with nose.tools.assert_raises(TypeError):
        canvas.data_range("fish")
