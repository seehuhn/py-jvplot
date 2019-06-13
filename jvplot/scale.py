#! /usr/bin/env python3
# scales.py - code to generate axis ticks and labels
# Copyright (C) 2019 Jochen Voss <voss@seehuhn.de>
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


class Linear:

    def __init__(self, pad=False):
        self.pad = pad

    def limits(self, a, b, constraint=None):
        a_width = self._get_aspect(constraint)
        if a_width:
            m = (a + b) / 2
            return m - a_width / 2, m + a_width / 2
        return a, b

    def within(self, a, b, constraint=None):
        a_width = self._get_aspect(constraint)
        if a_width:
            step = self._smallest_scale_larger_than(a_width)
        else:
            step = self._smallest_scale_larger_than(b - a)

        while True:
            step -= 1

            dx = self._scale_length(step)
            ia = math.ceil(a / dx)
            ib = math.floor(b / dx)
            while a_width and (ib - ia) * dx > a_width:
                if a - ia * dx > ib * dx - b:
                    ia += 1
                else:
                    ib -= 1
            ticks = [i * dx for i in range(ia, ib+1)]
            if len(ticks) >= 2:
                yield ticks, self._labels(ticks)

    def over(self, a, b, constraint):
        a_width = self._get_aspect(constraint)
        if a_width:
            step = self._smallest_scale_larger_than(a_width)
        else:
            step = self._smallest_scale_larger_than(b - a)

        while True:
            dx = self._scale_length(step)
            ia = math.floor(a / dx)
            ib = math.ceil(b / dx)
            while a_width and (ib - ia + 1) * dx < a_width:
                if a - ia * dx < ib * dx - b:
                    ia -= 1
                else:
                    ib += 1
            ticks = [i * dx for i in range(ia, ib+1)]
            if len(ticks) >= 2:
                yield ticks, self._labels(ticks)
            step -= 1

    def _labels(self, ticks):
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

    @staticmethod
    def _scale_length(k):
        """Get the scale length k.

        Scale lengths are indexed by integers k, and are ..., 0.1, 0.2,
        0.25, 0.5, 1.0, 2.0, 2.5, 5.0, 10.0, ..., where k=0 corresponds to
        the scale length 1.0 and larger values of k correspond to larger
        scale lengths.

        """
        c = [1.0, 2.0, 2.5, 5.0][k % 4]
        return c * 10**(k//4)

    @staticmethod
    def _smallest_scale_larger_than(x):
        """Get the smallest scale with scale length >=x.  This corresponds to
        rounding up to the nearest scale length.

        """
        q = 10**0.25 / 2
        k = math.floor(math.log10(q * x) * 4) + 1
        if Linear._scale_length(k) <= x:
            k += 1
        return k

    @staticmethod
    def _get_aspect(constraint):
        aspect = None
        if constraint:
            for key, val in constraint.items():
                if key == "aspect":
                    aspect = val
                else:
                    msg = f"cannot use constraint {key!r} for linear scales"
                    raise ValueError(msg)
        return aspect
