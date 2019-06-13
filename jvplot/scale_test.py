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

def test_linear_ticks_within():
    l = scale.Linear()

    for a, b in [(0.01, 4.99), (-0.01, 5.01), (0, 1), (-1, 1), (0, 3.14159265)]:
        count = 0
        for ticks, _ in l.ticks_within(a, b):
            assert len(ticks) >= 2
            assert ticks[0] >= a
            assert ticks[-1] <= b
            assert ticks[0] - (ticks[1] - ticks[0]) < a
            assert ticks[-1] + (ticks[1] - ticks[0]) > b

            count += 1
            if count >= 5:
                break

def test_linear_ticks_over():
    l = scale.Linear()

    for a, b in [(0.01, 4.99), (-0.01, 5.01), (0, 1), (-1, 1), (0, 3.14159265)]:
        print()
        print(a, b)
        count = 0
        for ticks, _ in l.ticks_over(a, b):
            print(ticks)
            assert len(ticks) >= 2
            assert ticks[0] <= a
            assert ticks[1] > a
            assert ticks[-2] < b
            assert ticks[-1] >= b

            count += 1
            if count >= 5:
                break
