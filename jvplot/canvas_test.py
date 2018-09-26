#! /usr/bin/env python3

import nose.tools

from . import canvas
from . import color
from . import errors
from . import param
from . import plot
from . import util


def test_canvas_param():
    res = 100
    lw = '17pt'
    c1 = canvas.Canvas(None, [0, 0, 200, 400], res=res, parent=None,
                       style={'padding': '0pt',
                              'margin_left': '10%',
                              'margin_top': '20%',
                              'margin_bottom': '$margin_right',
                              'lw': lw})

    # parameter type 'width'
    key = 'margin_left'
    val = c1.get_param(key)
    nose.tools.assert_almost_equal(val, 0.1*200)

    # parameter type 'height'
    key = 'margin_top'
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

def test_plot_aspect():
    with plot.Plot("/dev/null", 3, 5) as pl:
        ax = pl.plot([1, 2, 3], [1, -1, 1], aspect=1)
        nose.tools.assert_almost_equal(ax.scale[0], ax.scale[1])
