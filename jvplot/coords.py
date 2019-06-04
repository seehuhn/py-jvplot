#! /usr/bin/env python3
# coords.py - code to position coordinate axis ticks
# Copyright (C) 2014-2018 Jochen Voss <voss@seehuhn.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import math
import numpy as np


class LinScaleFactoryFactory:

    def __init__(self, pad=False):
        self.pad = pad

    def __call__(self, width):
        base = _smallest_scale_larger_than(width)
        return LinScaleFactory(base)

    def labels(self, ticks):
        ll = ["%g"%x for x in ticks]
        if all("e" not in l for l in ll) and any("." in l for l in ll):
            parts = []
            for l in ll:
                s = l.split(".")
                if len(s) < 2:
                    s = (s[0], '0')
                parts.append(s)
            max_digits = max(len(b) for _, b in parts)
            ll = []
            for a, b in parts:
                b = b.ljust(max_digits, '0')
                ll.append(a + '.' + b)
        if self.pad:
            max_len = max(len(l) for l in ll)
            ll = [l.rjust(max_len) for l in ll]
        return ll

class LinScaleFactory:

    def __init__(self, base):
        self.base = base

    def __call__(self, level):
        spacing = _scale_length(self.base - level)
        return LinScale(spacing)

class LinScale:

    def __init__(self, spacing):
        self.spacing = spacing

    def __call__(self, i):
        return i * self.spacing

    def ceil(self, x):
        return math.ceil(x / self.spacing)

    def floor(self, x):
        return math.floor(x / self.spacing)


def ticks_inside(sff, a, b, max_ticks=20):
    """A generator for axis tick suggestions.

    This produces lists of proposed tick label positions inside the
    interval [a, b].

    """

    assert a < b, f"error: {a} !< {b}"
    factory = sff(b - a)
    level = 1
    while True:
        scale = factory(level)
        i0 = scale.ceil(a)
        i1 = scale.floor(b)
        ticks = [scale(i) for i in range(i0, i1+1)]
        if len(ticks) > max_ticks:
            break
        if len(ticks) >= 2:
            yield (a, b), ticks
        level += 1

def ticks_over(sff, a, b, max_ticks=20):
    """A generator for axis tick suggestions.

    This produces lists of proposed tick label positions which cover
    the interval [a, b].

    """

    factory = sff(b - a)
    level = 0
    while True:
        scale = factory(level)
        i0 = scale.floor(a)
        i1 = scale.ceil(b)
        ticks = [scale(i) for i in range(i0, i1+1)]
        if len(ticks) > max_ticks:
            break
        if len(ticks) >= 2:
            yield (ticks[0], ticks[-1]), ticks
        level += 1

def ticks_over_bounded(sff, a, b, max_length, max_ticks=20):
    """A generator for axis tick suggestions.

    This produces lists of proposed tick label positions which cover
    the interval [a, b], but where the ticks can be contained in an
    interval of length max_length.

    """

    factory = sff(max_length)
    level = 1
    while True:
        scale = factory(level)
        i0 = scale.floor(a)
        i1 = scale.ceil(b)
        while True:
            if a - scale(i0) < scale(i1) - b:
                j0, j1 = i0 - 1, i1
            else:
                j0, j1 = i0, i1 + 1
            if scale(j1 - j0) > max_length:
                break
            i0, i1 = j0, j1
        ticks = [scale(i) for i in range(i0, i1+1)]
        if len(ticks) > max_ticks:
            break
        if len(ticks) > 2 and scale(i1 - i0) <= max_length:
            d = (max_length - ticks[-1] + ticks[0]) / 2
            yield (ticks[0]-d, ticks[-1]+d), ticks
        level += 1


class AxisPenalties:

    """Args:

    label_penalty_fn (optional): A function to check whether the
        labels overlap.  The function is called with three arguments:
        the device width, the tick locations in the range [0,
        device_width] (all in device coordinates), and the label
        strings.  It must return a positive value where 0 indicates
        perfect layout, larger values indicate worse layouts, and
        unacceptable layouts correspond to values greater than 1.

    """

    def __init__(self, dev_width, *, data_range=None, label_width_fn=None,
                 dev_tick_dist=None):
        self.dev_width = dev_width
        self.data_range = data_range
        self.label_width_fn = label_width_fn
        self.dev_tick_dist = dev_tick_dist

    def __call__(self, axis_range, ticks, labels):
        a, b = axis_range
        assert a <= ticks[0] < ticks[-1] <= b
        scale = self.dev_width / (b - a)

        pp = []

        # make sure the labels don't overlap
        if labels and self.label_width_fn:
            sep = self.label_width_fn("xx")
            xx = np.array([(x-a)*scale for x in ticks])
            ww = np.array([self.label_width_fn(l) for l in labels])
            l = xx - .5*ww
            r = xx + .5*ww
            dev_overlap = np.maximum(r[:-1] - l[1:] + sep, 0)
            p0 = np.sum(np.square(dev_overlap*2/sep))
            dev_outlap = np.maximum([-l[0], r[-1]-self.dev_width], 0)
            p1 = np.mean(np.square(dev_outlap/sep))
            pp.append(p0 + p1)

        # check that tick distances are close to the specified value
        if self.dev_tick_dist is not None:
            mean_dist = np.mean(np.array(ticks[1:]) - np.array(ticks[:-1]))
            dev_dist = mean_dist * scale
            pp.append(7*abs(math.log(dev_dist / self.dev_tick_dist, 5)))

        # make sure the ticks cover most of the axis range
        l = (ticks[0] - a) / (b - a)
        pp.append((4*l)**2)
        r = (b - ticks[-1]) / (b - a)
        pp.append((4*r)**2)

        # make sure the data has enough space
        if self.data_range is not None:
            d_data = self.data_range[1] - self.data_range[0]
            d_axis = b - a
            pp.append(abs(math.log2(d_axis / d_data)))

        return np.sum(np.square(pp))

def find_best(sff, penalties, *, axis_lim=None, axis_len=None):
    data_range = penalties.data_range
    if axis_lim is not None:
        assert axis_len is None
        pick = ticks_inside(sff, axis_lim[0], axis_lim[1])
    elif axis_len is not None:
        assert data_range is not None
        pick = ticks_over_bounded(sff, data_range[0], data_range[1], axis_len)
    else:
        assert data_range is not None
        pick = ticks_over(sff, data_range[0], data_range[1])

    best_penalty = np.infty
    best_axis_range = None
    best_ticks = None
    for axis_range, ticks in pick:
        labels = sff.labels(ticks)
        p = penalties(axis_range, ticks, labels)
        if p < best_penalty:
            best_penalty = p
            best_axis_range = axis_range
            best_ticks = ticks

    return best_penalty, best_axis_range, best_ticks


def _scale_length(k):

    """Get the scale length k.

    Scale lengths are indexed by integers k, and are ..., 0.1, 0.2,
    0.25, 0.5, 1.0, 2.0, 2.5, 5.0, 10.0, ..., where k=0 corresponds to
    the scale length 1.0 and larger values of k correspond to larger
    scale lengths.

    """
    c = [1.0, 2.0, 2.5, 5.0][k % 4]
    return c * 10**(k//4)

def _smallest_scale_larger_than(x):
    """Get the smallest scale with scale length >=x.  This corresponds to
    rounding up to the nearest scale length.

    """
    q = 10**0.25 / 2
    k = math.floor(math.log10(q * x) * 4) + 1
    if _scale_length(k) <= x:
        k += 1
    return k
