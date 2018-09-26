#! /usr/bin/env python3

import numpy as np

import nose.tools

from . import coords


def test_ticks_inside():
    sff = coords.LinScaleFactoryFactory()
    n = 100
    aa = np.random.uniform(0, 1, size=n)
    bb = aa + 10**np.random.uniform(-3, 2, size=n)
    for a, b in zip(aa, bb):
        count = 0
        for axis_range, ticks in coords.ticks_inside(sff, a, b):
            count += 1
            assert 2 <= len(ticks) <= 20
            assert a <= ticks[0] < ticks[-1] <= b
            assert axis_range[0] <= ticks[0] < ticks[-1] <= axis_range[1]
        assert count > 0

def test_ticks_over():
    sff = coords.LinScaleFactoryFactory()
    n = 100
    aa = np.random.uniform(0, 1, size=n)
    bb = aa + 10**np.random.uniform(-3, 2, size=n)
    for a, b in zip(aa, bb):
        count = 0
        for axis_range, ticks in coords.ticks_over(sff, a, b):
            count += 1
            assert 2 <= len(ticks) <= 20
            assert axis_range[0] <= ticks[0] <= a < b <= ticks[-1] <= axis_range[1]
        assert count > 0

def test_ticks_bounded():
    sff = coords.LinScaleFactoryFactory()
    n = 100
    aa = np.random.uniform(0, 1, size=n)
    bb = aa + 10**np.random.uniform(-3, 2, size=n)
    ll = (bb - aa) * 10**np.random.uniform(0.1, 2, size=n)
    for a, b, max_length in zip(aa, bb, ll):
        count = 0
        for axis_range, ticks in coords.ticks_over_bounded(sff, a, b, max_length):
            count += 1
            assert 2 <= len(ticks) <= 20
            assert axis_range[0] <= ticks[0] <= a < b <= ticks[-1] <= axis_range[1]
            assert ticks[-1] - ticks[0] <= max_length
        assert count > 0

def test_fish():
    x_sff = coords.LinScaleFactoryFactory()
    label_width_fn = lambda s: len(s)*7
    x_range = (0.123, 1.234)

    x_penalties = coords.AxisPenalties(4*72, data_range=x_range,
                                       label_width_fn=label_width_fn)
    coords.find_best(x_sff, x_penalties)

def test_scale_length():
    assert coords._scale_length(0) == 1
    nose.tools.assert_almost_equal(coords._scale_length(1), 2)
    nose.tools.assert_almost_equal(coords._scale_length(2), 2.5)
    nose.tools.assert_almost_equal(coords._scale_length(3), 5)
    nose.tools.assert_almost_equal(coords._scale_length(4), 10)

def test_smallest_scale_larger_than():
    for x in np.linspace(0.1, 100, 1000):
        k = coords._smallest_scale_larger_than(x)
        y = coords._scale_length(k)
        assert y > x, "%f (tick %d) > %f failed" % (y, k, x)
        z = coords._scale_length(k-1)
        assert z <= x, "%f (tick %d) <= %f failed" % (z, k-1, x)
