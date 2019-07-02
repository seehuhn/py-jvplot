#! /usr/bin/env python3

import numpy as np

import pytest

from . import scale


def test_scale_length():
    l = scale.Linear()
    assert l._scale_length(0) == 1
    assert l._scale_length(1) == pytest.approx(2)
    assert l._scale_length(2) == pytest.approx(2.5)
    assert l._scale_length(3) == pytest.approx(5)
    assert l._scale_length(4) == pytest.approx(10)

def test_smallest_scale_larger_than():
    l = scale.Linear()
    for x in np.linspace(0.1, 100, 1000):
        k = l._smallest_scale_larger_than(x)
        y = l._scale_length(k)
        assert y > x, "%f (tick %d) > %f failed" % (y, k, x)
        z = l._scale_length(k-1)
        assert z <= x, "%f (tick %d) <= %f failed" % (z, k-1, x)

def test_linear_ticks():
    l = scale.Linear()

    ranges = [
        (0.01, 4.99),
        (-0.01, 5.01),
        (0.01, 5.01),
        (0, 1),
        (-1, 1),
        (0, 3.14159265)
    ]

    for a, b in ranges:
        count = 0
        for lim, ticks, _ in l.ticks(a, b, allow_outside=False):
            assert len(ticks) >= 2
            d = ticks[1] - ticks[0]

            assert lim[0] == a and lim[1] == b
            assert ticks[0] >= a
            assert ticks[0] - d < a
            assert ticks[-1] <= b
            assert ticks[-1] + d > b

            count += 1
            if count >= 6:
                break

    for a, b in ranges:
        count = 0
        for lim, ticks, _ in l.ticks(a, b):
            assert len(ticks) >= 2
            d = ticks[1] - ticks[0]

            assert lim[0] <= min(ticks[0], a)
            assert lim[1] >= max(ticks[-1], b)
            assert ticks[0] - d < a
            assert ticks[0] + d > a
            assert ticks[-1] - d < b
            assert ticks[-1] + d > b

            count += 1
            if count >= 6:
                break

def test_ticks_for_width():
    l = scale.Linear()

    cases = [
        (0, 1, 1),
        (-0.3, 4.5, 5),
        (-0.3, 4.5, 0.5),
        (0.2, 5.2, 5),
    ]

    for a, b, w in cases:
        count = 0
        for lim, ticks, labels in l.ticks(a, b, width=w):
            assert len(ticks) >= 2
            d = ticks[1] - ticks[0]
            eps = 1e-6 * d

            assert abs(lim[1] - lim[0] - w) < 1e-6
            assert lim[0] - eps <= ticks[0] < lim[0] + d + eps
            assert lim[1] - d - eps < ticks[-1] <= lim[1] + eps

            count += 1
            if count >= 6:
                break
