import nose.tools

from . import canvas
from . import color
from . import errors
from . import param
from . import util


def test_canvas_param():
    res = 100
    lw = '17pt'
    c1 = canvas.Canvas(None, 0, 0, 200, 400, res=res, parent=None,
                       style={'margin.left': '10%',
                              'margin.top': '20%',
                              'margin.bottom': '$margin.right',
                              'lw': lw})

    # parameter type 'width'
    key = 'margin.left'
    val = c1.get_param(key)
    nose.tools.assert_almost_equal(val, 0.1*200)

    # parameter type 'height'
    key = 'margin.top'
    val = c1.get_param(key)
    nose.tools.assert_almost_equal(val, 0.2*400)

    # parameter type 'dim'
    key = 'font_size'
    val = c1.get_param(key)
    assert val == util._convert_dim(param.default[key][1], res)

    # parameter type 'col'
    key = 'line_col'
    val = c1.get_param(key)
    assert val == color.get(param.default[key][1])

    # parameter type 'bool'
    key = 'plot_point_separate'
    val = c1.get_param(key)
    assert val == param.default[key][1]

    # variables
    key = 'plot_lw'             # default value is '$lw'
    val = c1.get_param(key)
    nose.tools.assert_almost_equal(val, util._convert_dim(lw, res))

    # inheritance
    font_size1 = '19mm'
    font_size2 = '21mm'
    c2 = canvas.Canvas(None, 50, 100, 100, 200, res=res, parent=c1,
                       style={'font_size': font_size1})
    key = 'font_size'
    val = c2.get_param(key)     # value taken from c2
    nose.tools.assert_equal(val, util._convert_dim(font_size1, res))
    val = c2.get_param(key, style={key: font_size2}) # ... from explicit style
    assert val == util._convert_dim(font_size2, res)
    key = 'lw'
    val = c2.get_param(key)     # ... from c1
    assert val == util._convert_dim(lw, res)
    key = 'axis_label_dist'
    val = c2.get_param(key)     # ... from param.default
    assert val == util._convert_dim(param.default[key][1], res)

    # inheritance and relative values
    key = 'margin.left'
    val = c2.get_param(key)     # c1 has '10%', percentage applies to c2.width
    nose.tools.assert_almost_equal(val, 0.1*100)

    # inheritance and variables
    key = 'margin.bottom'
    # c1 has '$margin.right', the latter taken from explicit style
    val = c2.get_param(key, style={'margin.right': '10px'})
    nose.tools.assert_equal(val, util._convert_dim('10px', res))

    # invalid parameter names
    with nose.tools.assert_raises(errors.InvalidParameterName):
        # mis-spelled 'font_size'
        canvas.Canvas(None, 50, 100, 100, 200, res=res, parent=c1,
                       style={'font.size': font_size1})
    with nose.tools.assert_raises(errors.InvalidParameterName):
        # mis-spelled 'font_size'
        c2.get_param('font.size')
    with nose.tools.assert_raises(errors.InvalidParameterName):
        # mis-spelled 'font_size'
        c2.get_param('font_size', style={'font.size': '10px'})
