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


class Linear:

    """

    :Arguments:

        data_range
            The data range to display, in data coordinates.
    """

    def __init__(self, data_range, lim=None):
        self.data_range = data_range
        self.lim = lim

    def __str__(self):
        if self.lim:
            return f"<coords.Linear {self.lim[0]}-{self.lim[1]} fixed>"
        return f"<coords.Linear {self.data_range[0]}-{self.data_range[1]}>"

    def try_single(self, *, length=None):
        """Generate a selection of plausible axis tick placements.  This
        generator yields 2-tuples containing the suggested axis limits and
        tick label positions.

        """
        if self.lim is not None:
            a, b = self.lim
            if length is not None and abs((b - a) / length - 1) > 1e-3:
                return

            k0 = _smallest_scale_larger_than(b - a)
            for k in range(k0 - 5, k0):
                spacing = _scale_length(k)
                i0 = math.ceil(a / spacing)
                i1 = math.floor(b / spacing)
                ticks = [k * spacing for k in range(i0, i1+1)]
                if len(ticks) > 1:
                    yield self.lim, ticks
        elif length is not None:
            a, b = self.data_range
            if b - a > length:
                return
            k0 = _smallest_scale_larger_than(length)
            for k in range(k0 - 5, k0):
                spacing = _scale_length(k)

                if 0 <= a and b <= length:
                    i0 = 0
                    i1 = math.floor(length / spacing)
                    a = 0
                    b = i1 * spacing
                elif -length <= a and b <= 0:
                    i0 = -math.floor(length / spacing)
                    i1 = 0
                    a = i0 * spacing
                    b = 0
                else:
                    i0 = math.ceil(a / spacing)
                    i1 = math.floor(b / spacing)
                    while True:
                        if i1 * spacing - b < a - i0 * spacing:
                            if (i1+1) * spacing - a > length:
                                break
                            i1 += 1
                            b = i1 * spacing
                        else:
                            if b - (i0-1)*spacing > length:
                                break
                            i0 -= 1
                            a = i0 * spacing
                assert a <= i0*spacing <= i1*spacing <= b
                d = length - (b - a)
                if d > 0:
                    a -= d / 2
                    b += d / 2
                ticks = [k * spacing for k in range(i0, i1+1)]
                if len(ticks) > 1:
                    yield (a, b), ticks
        else:
            a, b = self.data_range
            k0 = _smallest_scale_larger_than(b - a)
            for k in range(k0 - 4, k0 + 1):
                spacing = _scale_length(k)
                i0 = math.floor(a / spacing)
                i1 = math.ceil(b / spacing)
                ticks = [k * spacing for k in range(i0, i1+1)]
                yield (i0*spacing, i1*spacing), ticks
                if len(ticks) > 2:
                    yield (a, i1*spacing), ticks[1:]
                    yield (i0*spacing, b), ticks[:-1]
                if len(ticks) > 3:
                    yield (a, b), ticks[1:-1]


    def penalties(self, width, axis_range, ticks, label_width, label_sep, best_tick_dist):
        """Compute the 4 penalty values for a given axis tick configuration.

        :Arguments:

        width
            The total axis width in device coordinate units.
        axis_range
            The axis range, in data coordinates.  This typically comes
            from output of the try_single() method.
        ticks
            List of tick locations in data coordinates, in increasing
            order.  This typically comes from output of the
            try_single() method.
        label_width
            The width/height of labels, in device coordinates.  This
            can be either ``None`` (for no labels) or a list of
            numeric widths.  In the latter case, ``labels`` and ``ticks``
            must have the same length.
        label_sep
            The minimal allowed distance between labels, in device
            coordinate units.
        best_tick_dist
            The optimal distance between axis ticks, in device coordinate
            units.

        """
        scale = width / (axis_range[1] - axis_range[0])

        p0 = 0.0
        if label_width is not None:
            for i in range(1, len(label_width)):
                dev_length = .5 * (label_width[i-1] + label_width[i]) + label_sep
                data_length = dev_length / scale
                space = ticks[i] - ticks[i-1]
                overlap = data_length - space
                if overlap > 0:
                    p0 += 1 + overlap / data_length

        p1 = 0.0
        if len(ticks) > 1:
            mean_dist = np.mean(np.array(ticks[1:]) - np.array(ticks[:-1]))
            p1 = abs(math.log(mean_dist * scale / best_tick_dist))

        p2 = 0.0
        if len(ticks) > 1:
            q_left = axis_range[0] / (ticks[1] - ticks[0])
            p2 += (math.ceil(q_left) - q_left)**2
            q_right = axis_range[1] / (ticks[-1] - ticks[-2])
            p2 += (q_right - math.floor(q_right))**2

        d_axis = axis_range[1] - axis_range[0]
        d_data = self.data_range[1] - self.data_range[0]
        p3 = abs(math.log2(d_axis / d_data))

        return [p0, p1, p2, p3]

def ranges_and_ticks(w, h, x_scale, y_scale, label_width, label_height,
                     label_sep, best_tick_dist, *, aspect=None):
    if aspect is None:
        best_p = np.inf
        for x_range, x_ticks in x_scale.try_single():
            pp = x_scale.penalties(w, x_range, x_ticks, label_width(x_ticks),
                                   label_sep, best_tick_dist)
            p = np.sum(pp)
            if p < best_p:
                best_p = p
                best_x_range = x_range
                best_x_ticks = x_ticks

        best_p = np.inf
        for y_range, y_ticks in y_scale.try_single():
            pp = y_scale.penalties(w, y_range, y_ticks, label_height(y_ticks),
                                   label_sep, best_tick_dist)
            p = np.sum(pp)
            if p < best_p:
                best_p = p
                best_y_range = y_range
                best_y_ticks = y_ticks
    else:
        best_p = np.inf
        for x_range, x_ticks in x_scale.try_single():
            pp = x_scale.penalties(w, x_range, x_ticks, label_width(x_ticks),
                                   label_sep, best_tick_dist)
            px = np.sum(pp)

            l = (x_range[1] - x_range[0]) * aspect * w / h
            for y_range, y_ticks in y_scale.try_single(length=l):
                pp = y_scale.penalties(w, y_range, y_ticks, label_height(y_ticks),
                                       label_sep, best_tick_dist)
                py = np.sum(pp)

                p = px + py
                if p < best_p:
                    best_p = p
                    best_x_range = x_range
                    best_x_ticks = x_ticks
                    best_y_range = y_range
                    best_y_ticks = y_ticks

        for y_range, y_ticks in y_scale.try_single():
            pp = y_scale.penalties(w, y_range, y_ticks, label_height(y_ticks),
                                   label_sep, best_tick_dist)
            py = np.sum(pp)

            l = (y_range[1] - y_range[0]) / aspect / w * h
            for x_range, x_ticks in x_scale.try_single(length=l):
                pp = x_scale.penalties(w, x_range, x_ticks, label_width(x_ticks),
                                       label_sep, best_tick_dist)
                px = np.sum(pp)

                p = px + py
                if p < best_p:
                    best_p = p
                    best_x_range = x_range
                    best_x_ticks = x_ticks
                    best_y_range = y_range
                    best_y_ticks = y_ticks

    return best_x_range, best_x_ticks, best_y_range, best_y_ticks


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
