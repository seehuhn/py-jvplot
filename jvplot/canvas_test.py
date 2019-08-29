#! /usr/bin/env python3

import pytest

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
    assert val == pytest.approx(0.1*200)

    # parameter type 'height'
    key = 'margin_top'
    val = c1.get_param(key)
    assert val == pytest.approx(0.2*400)

    # parameter type 'dim'
    key = 'font_size'
    val = c1.get_param(key)
    assert val == util.convert_dim(param.DEFAULT[key][1], res)

    # parameter type 'col'
    key = 'fg_col'
    val = c1.get_param(key)
    assert val == color.get(param.ROOT[key])

    # parameter type 'bool'
    key = 'plot_point_separate'
    val = c1.get_param(key)
    assert val == param.DEFAULT[key][1]

    # variables
    key = 'plot_lw'             # default value is '$lw'
    val = c1.get_param(key)
    assert val == pytest.approx(util.convert_dim(lw, res))

    # invalid parameter names
    with pytest.raises(errors.InvalidParameterName):
        # mis-spelled 'font_size'
        canvas.Canvas(None, [50, 100, 100, 200], res=res, parent=c1,
                      style={'font.size': '10px'})
    with pytest.raises(errors.InvalidParameterName):
        # mis-spelled 'font_size'
        c1.get_param('font.size')
    with pytest.raises(errors.InvalidParameterName):
        # mis-spelled 'font_size'
        c1.get_param('font_size', style={'font.size': '10px'})

def test_axes():
    with plot.Plot('/dev/null', '3in', '5in') as pl:
        with pytest.raises(ValueError):
            # need {x,y}_range or {x,y}_lim
            pl.axes()

        # try axes with limits but no data range
        ax = pl.axes(x_lim=[0, 1], y_lim=[0, 1])

def test_plot_aspect():
    for asp in [.5, 1, 2]:
        with plot.Plot('/dev/null', '3in', '5in') as pl:
            ax = pl.plot([1, 2, 4], [1, -1, 1], aspect=asp)
            assert ax.scale[0]/ax.scale[1] == pytest.approx(asp)

def test_axes_aspect():
    for asp in [.5, 1, 2]:
        with plot.Plot('/dev/null', '3in', '5in') as pl:
            ax = pl.axes(x_range=[0, 1], y_range=[0, 2], aspect=asp)
            assert ax.scale[0]/ax.scale[1] == pytest.approx(asp)

def test_grid_plot():
    ranges = [(0,1), (0,1), (1,2)]
    m = len(ranges)
    with plot.Plot('/dev/null', '3in', '5in') as pl:
        grid = pl.grid_plot(ranges)
        assert grid.shape == (m, m)
