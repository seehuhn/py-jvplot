#! /usr/bin/env python3

import unittest

import numpy as np

import nose.tools

from . import coords
from . import plot


def test_linear_simple():
    rnge = (0.1, 1.0)
    cc = coords.Linear(rnge)
    for (a, b), ticks in cc.try_single():
        assert len(ticks) > 1
        assert a <= rnge[0]
        assert a <= ticks[0]
        assert ticks[-1] <= b
        assert rnge[1] <= b

def test_linear_with_limit():
    cases = [
        (0.1, 0.9),
        (0.5, 1.37),
        (1.1, 1.9),
        (0.9773, 0.9774),
    ]
    lim = (0.05, 1.05)
    for data_range in cases:
        cc = coords.Linear(data_range, lim=lim)
        count = 0
        for (a, b), ticks in cc.try_single():
            assert len(ticks) > 1
            assert (a, b) == lim
            assert a <= ticks[0]
            assert ticks[-1] <= b
            count += 1
        assert count > 0

    cc = coords.Linear((1, 2), lim=(0, 1))
    count = 0
    for (a, b), ticks in cc.try_single(length=1.1):
        count += 1
    assert count == 0

def test_linear_with_aspect():
    cases = [
        (1, (0.1, 0.9)),
        (1, (-0.3, -0.25)),
        (1, (0.5, 1.37)),
        (1.05, (1.1, 1.9)),
        (1.05, (2.9773, 2.9774)),
    ]
    for length, data_range in cases:
        cc = coords.Linear(data_range)
        count = 0
        for (a, b), ticks in cc.try_single(length=length):
            assert len(ticks) > 1
            assert a <= data_range[0]
            assert a <= ticks[0] + 1e-6
            assert ticks[-1] - 1e-6 <= b
            assert data_range[1] <= b
            assert abs(b - a - length) < 1e-6
            count += 1
        assert count > 0

def test_combined():
    cases = [
        [(0.123, 0.987), (0.333, 0.832)],
    ]
    for x_range, y_range in cases:
        cx = coords.Linear(x_range)
        cy = coords.Linear(y_range)
        for asp in [None, 0.8, 1.0, 1.2]:
            xa, xt, ya, yt = coords.ranges_and_ticks(
                100, 100, cx, cy,
                lambda x: [len("%g"%xi)*7 for xi in x],
                lambda x: [10 for xi in x],
                10, 20, aspect=asp)
            assert 1 < len(xt) < 10
            assert 1 < len(yt) < 10
            if asp is not None:
                nose.tools.assert_almost_equals(
                    (ya[1] - ya[0]) / (xa[1] - xa[0]), asp)

def test_scale_length():
    assert coords._scale_length(0) == 1
    nose.tools.assert_almost_equals(coords._scale_length(1), 2)
    nose.tools.assert_almost_equals(coords._scale_length(2), 2.5)
    nose.tools.assert_almost_equals(coords._scale_length(3), 5)
    nose.tools.assert_almost_equals(coords._scale_length(4), 10)

def test_smallest_scale_larger_than():
    for x in np.linspace(0.1, 100, 1000):
        k = coords._smallest_scale_larger_than(x)
        y = coords._scale_length(k)
        assert y > x, "%f (tick %d) > %f failed" % (y, k, x)
        z = coords._scale_length(k-1)
        assert z <= x, "%f (tick %d) <= %f failed" % (z, k-1, x)

def test_tall_axes():
    # make the y-axis much taller than the x-axis
    ax_x = coords.Linear((0, 10))
    ax_y = coords.Linear((0, 8))
    w = 118.49244249201104
    h = 346.0514976101213
    def width_fn(ticks):
        labels = ["%g" % xi for xi in ticks]
        return [7.695 * len(label) for label in labels]
    def height_fn(ticks):
        return [13.837 for _ in ticks]
    label_sep = 8.302200083022
    opt_spacing = 78.74015748031495
    aspect = 1
    print("---")
    xa, xt, ya, yt = coords.ranges_and_ticks(
        w, h, ax_x, ax_y, width_fn, height_fn,
        label_sep, opt_spacing, aspect=aspect)
    print("---")
    # assert that the longer axis has more labels
    assert len(yt) > len(xt)

class CoordsPenaltyTestCase(unittest.TestCase):

    def setUp(self):
        self.plot = plot.Plot('/dev/null', 5, 3)
        self.ax = self.plot.viewport(self.plot.rect, (0, 1), (0, 3))

    def tearDown(self):
        self.plot.close()

    def test_p0(self):
        label = "hello"
        labels = [label, label]

        # horizontal axis
        h_ext = self.ax.ctx.text_extents(label)
        dev_width = h_ext[4]
        widths = [dev_width, dev_width]
        width = dev_width / self.ax.scale[0]
        cc = coords.Linear((0, 1))

        ticks = [0, width]
        p = cc.penalties(self.ax.rect[2], (0, 1), ticks, widths, 0.0, 1.0)

        ticks = [0, 2*width]
        p = cc.penalties(self.ax.rect[2], (0, 1), ticks, widths, 0.0, 1.0)
        nose.tools.assert_almost_equals(p[0], 0)

        ticks = [0, .5*width]
        p = cc.penalties(self.ax.rect[2], (0, 1), ticks, widths, 0.0, 1.0)
        nose.tools.assert_almost_equals(p[0], 1 + .5)

        ticks = [0, width]
        p = cc.penalties(self.ax.rect[2], (0, 1), ticks, widths, h_ext[4], 1.0)
        nose.tools.assert_almost_equals(p[0], 1 + .5)

        # vertical axis
        v_ext = self.ax.ctx.font_extents()
        dev_heigth = v_ext[2]
        heights = [dev_heigth, dev_heigth]
        height = dev_heigth / self.ax.scale[1]
        cc = coords.Linear((0, 3))

        ticks = [0, height]
        p = cc.penalties(self.ax.rect[3], (0, 3), ticks, heights, 0.0, 1.0)
        nose.tools.assert_almost_equals(p[0], 0)

        ticks = [0, 2*height]
        p = cc.penalties(self.ax.rect[3], (0, 3), ticks, heights, 0.0, 1.0)
        nose.tools.assert_almost_equals(p[0], 0)

        ticks = [0, .5*height]
        p = cc.penalties(self.ax.rect[3], (0, 3), ticks, heights, 0.0, 1.0)
        nose.tools.assert_almost_equals(p[0], 1 + .5)

        ticks = [0, height]
        p = cc.penalties(self.ax.rect[3], (0, 3), ticks, heights, v_ext[2], 1.0)
        nose.tools.assert_almost_equals(p[0], 1 + .5)

        # no labels
        p = cc.penalties(self.ax.rect[3], (0, 3), ticks, None, v_ext[2], 1.0)
        nose.tools.assert_almost_equals(p[0], 0)

    def test_p1(self):
        cc = coords.Linear((0, 1))
        ticks = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
        p = cc.penalties(10, (0, 1), ticks, None, 1, 2.0)
        nose.tools.assert_almost_equals(p[1], 0)

    # TODO(voss): implement unit tests for p2

    def test_p3(self):
        cc = coords.Linear((0, 1))
        p = cc.penalties(self.ax.rect[3], (0, 1), [], [], 1, 1)
        nose.tools.assert_almost_equals(p[3], 0)
        p = cc.penalties(self.ax.rect[3], (0, 2), [], [], 1, 1)
        nose.tools.assert_almost_equals(p[3], 1.0)
