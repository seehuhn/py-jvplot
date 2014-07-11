import nose.tools

from .param import get

def test_param():
    res = 123
    style = {
        'does.not.exist.either': 12,
        'margin': '2in',
        'margin.top': '1in',
        'margin.right': '50%',
    }

    with nose.tools.assert_raises(ValueError):
        get('does.not.exist', res, style)
    with nose.tools.assert_raises(ValueError):
        get('does.not.exist.either', res, style)

    val = get('margin.top', res, style)
    nose.tools.eq_(val, res)
    val = get('margin.bottom', res, style)
    nose.tools.eq_(val, 2 * res)
    val = get('margin.right', res, style, parent_width=200)
    nose.tools.assert_almost_equals(val, 100)
