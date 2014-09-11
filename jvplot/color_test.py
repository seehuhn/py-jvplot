import nose.tools

from . import color


def test_color():
    r, g, b, a = color.get('#000000')
    assert r == g == b == 0.0
    assert a == 1.0

    r, g, b, a = color.get('#FFFFFF')
    assert r == g == b == 1.0
    assert a == 1.0

    r, g, b, a = color.get('#123456')
    nose.tools.assert_almost_equals(r, 0x12/255)
    nose.tools.assert_almost_equals(g, 0x34/255)
    nose.tools.assert_almost_equals(b, 0x56/255)
    assert a == 1.0

    r, g, b, a = color.get('#000')
    assert r == g == b == 0.0
    assert a == 1.0

    r, g, b, a = color.get('#FFF')
    assert r == g == b == 1.0
    assert a == 1.0

    r, g, b, a = color.get('#789')
    nose.tools.assert_almost_equals(r, 0x77/255)
    nose.tools.assert_almost_equals(g, 0x88/255)
    nose.tools.assert_almost_equals(b, 0x99/255)
    assert a == 1.0

    with nose.tools.assert_raises(ValueError):
        color.get('#01234G')

    r, g, b, a = color.get('red')
    assert r - 0.5 > max(g, b) >= 0.0
    assert a == 1.0

    r, g, b, a = color.get('rgba(0, 127.5, 255, 0.3)')
    nose.tools.assert_almost_equals(r, .0)
    nose.tools.assert_almost_equals(g, .5)
    nose.tools.assert_almost_equals(b, 1.0)
    nose.tools.assert_almost_equals(a, .3)
