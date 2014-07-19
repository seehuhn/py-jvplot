import nose.tools
import numpy as np

from .axes import _axis_tick_distance, _next_axis_tick, _axis_penalties

def test_axis_tick_distance():
    assert _axis_tick_distance(0) == 1
    nose.tools.assert_almost_equals(_axis_tick_distance(1), 2)
    nose.tools.assert_almost_equals(_axis_tick_distance(2), 2.5)
    nose.tools.assert_almost_equals(_axis_tick_distance(3), 5)
    nose.tools.assert_almost_equals(_axis_tick_distance(4), 10)

def test_next_axis_tick():
    for x in np.linspace(0.1, 100, 1001):
        k = _next_axis_tick(x)
        y = _axis_tick_distance(k)
        assert y > x, "%f (tick %d) > %f failed" % (y, k, x)
        z = _axis_tick_distance(k-1)
        assert z <= x, "%f (tick %d) <= %f failed" % (z, k-1, x)

def test_penalties():
    p = _axis_penalties((0, 1), (0, 1), [], [], True, None, 0, 0)
    nose.tools.assert_almost_equals(p[3], 0)
    p = _axis_penalties((0, 1), (0, 2), [], [], True, None, 0, 0)
    nose.tools.assert_almost_equals(p[3], 1.0)
