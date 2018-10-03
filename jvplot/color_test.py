import pytest

from . import color


def test_color():
    r, g, b, a = color.get('#000000')
    assert r == g == b == 0.0
    assert a == 1.0

    r, g, b, a = color.get('#FFFFFF')
    assert r == g == b == 1.0
    assert a == 1.0

    r, g, b, a = color.get('#123456')
    assert r == pytest.approx(0x12/255)
    assert g == pytest.approx(0x34/255)
    assert b == pytest.approx(0x56/255)
    assert a == 1.0

    r, g, b, a = color.get('#000')
    assert r == g == b == 0.0
    assert a == 1.0

    r, g, b, a = color.get('#FFF')
    assert r == g == b == 1.0
    assert a == 1.0

    r, g, b, a = color.get('#789')
    assert r == pytest.approx(0x77/255)
    assert g == pytest.approx(0x88/255)
    assert b == pytest.approx(0x99/255)
    assert a == 1.0

    with pytest.raises(ValueError):
        color.get('#01234G')

    r, g, b, a = color.get('red')
    assert r - 0.5 > max(g, b) >= 0.0
    assert a == 1.0

    r, g, b, a = color.get('rgba(0, 127.5, 255, 0.3)')
    assert r == pytest.approx(.0)
    assert g == pytest.approx(.5)
    assert b == pytest.approx(1.0)
    assert a == pytest.approx(.3)
