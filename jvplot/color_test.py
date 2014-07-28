import nose.tools

from . import color

def test_color():
    r, g, b, a = color.check('#000000')
    assert r == g == b == 0.0
    assert a == 1.0

    r, g, b, a = color.check('#FFFFFF')
    assert r == g == b == 1.0
    assert a == 1.0

    r, g, b, a = color.check('#123456')
    nose.tools.assert_almost_equals(r, 0x12/255)
    nose.tools.assert_almost_equals(g, 0x34/255)
    nose.tools.assert_almost_equals(b, 0x56/255)
    assert a == 1.0

    r, g, b, a = color.check('#000')
    assert r == g == b == 0.0
    assert a == 1.0

    r, g, b, a = color.check('#FFF')
    assert r == g == b == 1.0
    assert a == 1.0

    r, g, b, a = color.check('#789')
    nose.tools.assert_almost_equals(r, 0x77/255)
    nose.tools.assert_almost_equals(g, 0x88/255)
    nose.tools.assert_almost_equals(b, 0x99/255)
    assert a == 1.0

    with nose.tools.assert_raises(ValueError):
        color.check('#01234G')

    r, g, b, a = color.check('red')
    assert r - 0.5 > max(g, b) >= 0.0
    assert a == 1.0
