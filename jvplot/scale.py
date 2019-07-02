#! /usr/bin/env python3
# scale.py - code to generate axis ticks and labels
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


_FUDGE = 1e-6


class Linear:

    def __init__(self, pad_labels=False):
        self.pad_labels = pad_labels

    def ticks(self, a, b, *, allow_outside=True, width=None):
        if width is not None:
            return self.ticks_for_width(a, b, width)
        return self.ticks_for_interval(a, b, allow_outside=allow_outside)

    def ticks_for_width(self, a, b, width):
        """Generate lists of ticks for an interval of width `width`."""

        step = self._smallest_scale_larger_than(width)
        while True:
            step -= 1

            dx = self._scale_length(step)
            ia = math.floor(a / dx)
            ib = math.ceil(b / dx)

            eps = dx * _FUDGE

            while (ib - ia + 1) * dx <= width: # we can squeeze in more ticks
                if a - ia * dx <= ib * dx - b:
                    ia -= 1
                else:
                    ib += 1

            while ((ib - ia) * dx > width # the tick interval is too wide
                   or b - a <= width + eps and (ib * dx - a > width + eps
                                                or b - ia * dx > width + eps)):
                if a - ia * dx > ib * dx - b:
                    ia += 1
                else:
                    ib -= 1
            if ib - ia + 1 < 2:
                continue

            left = ia * dx
            right = ib * dx
            gap = width - right + left
            # minimize p => (left - p*gap - a)**2 + (right + (1-p)*gap - b)**2:
            # the derivative is
            #   -2*gap*(left - p*gap - a) - 2*gap*(right + (1-p)*gap - b)
            #   == -2*gap*(left - p*gap - a) - 2*gap*(right + gap - p*gap - b)
            #   == -2*gap*(left + right - (2*p - 1)*gap - a - b)
            # and thus the minimum satisfies
            p = ((left + right - a - b) / gap + 1) / 2 if gap > eps else 0
            if p <= 0:
                right = left + width
            elif p >= 1:
                left = right - width
            else:
                left -= p * gap
                right += (1 - p) * gap

            lim = [left, right]
            ticks = [i * dx for i in range(ia, ib+1)]
            labels = self._labels(ticks)
            yield lim, ticks, labels

    def ticks_for_interval(self, a, b, *, allow_outside=True):
        """Generate lists of ticks for the interval [a,b]."""

        step = self._smallest_scale_larger_than(b - a)
        # At step size `step`, at most one tick can be inside the
        # range.

        while True:
            dx = self._scale_length(step)
            ia = math.floor(a / dx)
            ib = math.ceil(b / dx)
            # Initially, there are two ticks outside (a, b).

            eps = dx * _FUDGE
            for _ in range(3):
                if ib+1 - ia < 2:
                    break
                all_inside = ia*dx + eps >= a and ib*dx - eps <= b
                if allow_outside or all_inside:
                    lim = (min(ia * dx, a), max(ib * dx, b))
                    ticks = [i * dx for i in range(ia, ib+1)]
                    labels = self._labels(ticks)
                    yield lim, ticks, labels

                if all_inside:
                    break

                # remove the tick which is furthest out
                if a - ia * dx > ib * dx - b:
                    ia += 1
                else:
                    ib -= 1

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
        if self.pad_labels:
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
