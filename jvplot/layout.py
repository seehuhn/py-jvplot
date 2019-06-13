#! /usr/bin/env python3

import itertools
import math

import numpy as np
import scipy.optimize as opt


class Layout:

    def __init__(self, dev_width, dev_padding, data_range, *,
                 lim=None, ticks=None, dev_opt_dist=None, labels=None,
                 dev_width_fn=None, can_shift=False, scale=None):
        """Create a new layout object.

        Args:
            dev_width (number): axis length in device units.
            dev_padding (number): width of padding at both edges, in
                device coordinates.
            data_range (2-tuple): the minimum and maximum data value
                to cover.
            lim (2-tuple, optional): a pair (x0, x1), where x0 is the
                data value corresponding to the inside of the
                left/bottom margin, and x1 is the data value for the
                inside of the right/top margin.
            ticks (list of numbers, optional): a list of data
                coordinate for the axis ticks.
            dev_opt_dist (number, optional): optimal tick distance in
                device coordinates.
            labels (list of strings, optional): a list of tick labels.
            dev_width_fn (function, optional): a function to determine
                the extent of a label text along the axis, in device
                coordinates.
            can_shift (bool): whether the labels can be shifted along
                the axis to avoid label collisions.
            scale: A coordinate scale to generate proposed ticks and
                labels.

        """
        self.dev_width = dev_width
        self.dev_padding = dev_padding
        self.data_range = data_range
        self.lim = lim
        self.ticks = ticks
        self.dev_opt_dist = dev_opt_dist
        self.labels = labels
        self.dev_width_fn = dev_width_fn
        self.can_shift = can_shift
        self.scale = scale

        self.shift = None

    def ticks_within(self, a, b, constraint=None, *, num=5):
        count = 0
        for ticks, labels in self.scale.within(a, b, constraint):
            yield ticks, labels
            count += 1
            if count >= num:
                break

    def ticks_over(self, a, b, constraint=None, *, num=5):
        count = 0
        for ticks, labels in self.scale.over(a, b, constraint):
            yield ticks, labels
            count += 1
            if count >= num:
                break

    def set_limits(self, constraint=None):
        a, b = self.data_range
        if self.ticks:
            if self.ticks[0] < a:
                a = self.ticks[0]
            if self.ticks[-1] > b:
                b = self.ticks[-1]
        self.lim = self.scale.limits(a, b, constraint)

    def range_penalty(self):
        penalty = 0
        rel_pad = self.dev_padding / (self.dev_width - 2*self.dev_padding)

        x0, x1 = self.lim
        left = (self.data_range[0] - x0) / (x1 - x0)
        right = (x1 - self.data_range[1]) / (x1 - x0)
        for val in [left, right]:
            if val < -rel_pad:
                penalty += 100 + abs(val) - rel_pad
            elif val < 0:
                penalty += 100 * abs(val) / rel_pad
            else:
                penalty += val
        return penalty

    def tick_penalty(self):
        if not self.ticks:
            return 0

        n = len(self.ticks)
        if n < 2:
            return 100

        x0, x1 = self.lim

        w = self.dev_width - 2*self.dev_padding
        q = w / (x1 - x0)
        dev_opt_dist = self.dev_opt_dist

        penalty = 0
        if self.ticks[0] >= x0:
            penalty += q * (self.ticks[0] - x0) / dev_opt_dist
        else:
            penalty += 100 + q * (x0 - self.ticks[0])
        for i in range(1, n):
            dt = self.ticks[i] - self.ticks[i-1]
            dev_dt = q * dt
            penalty += abs(math.log2(dev_dt / dev_opt_dist)) / (n - 1)
        if self.ticks[-1] <= x1:
            penalty += q * (x1 - self.ticks[-1]) / dev_opt_dist
        else:
            penalty += 100 + q * (self.ticks[-1] - x1)
        return penalty

    def label_penalty(self):
        if not self.labels:
            return 0

        dev_width_fn = self.dev_width_fn
        x0, x1 = self.lim

        q = (self.dev_width - 2*self.dev_padding) / (x1 - x0)
        pos = [self.dev_padding + (xi - x0)*q for xi in self.ticks]
        widths = [dev_width_fn(si) for si in self.labels]

        sep = dev_width_fn("10")

        pos = np.array(pos)
        widths = np.array(widths)
        def loss(shift):
            l = pos - shift * widths
            r = pos + (1-shift) * widths

            a = np.sum(np.square(np.maximum([-l[0], r[-1] - self.dev_width], 0)))
            b = np.sum(np.square(np.maximum(r[:-1] - l[1:] + sep, 0)))
            c = np.sum(np.square((shift - .5) * sep))
            return 100 * a + 10 * b + c
        n = len(self.ticks)
        shift = np.repeat(.5, n)
        if self.can_shift:
            res = opt.minimize(loss, shift, bounds=[(0, 1)]*n, method='L-BFGS-B')
            shift = res.x
        self.shift = shift

        l = pos - shift * widths
        r = pos + (1-shift) * widths
        penalty = 0
        if l[0] < 0:
            penalty += 100 + (-l[0]) / sep
        if r[-1] > self.dev_width:
            penalty += 100 + (r[-1] - self.dev_width) / sep
        d = np.maximum((r[:-1] - l[1:]) / sep + 1, 0)
        penalty += 100 * np.amax(d)
        penalty += np.mean(np.square((shift - .5) * sep))

        return penalty

    def penalty(self):
        p1 = self.range_penalty()
        p2 = self.tick_penalty()
        p3 = self.label_penalty()
        # print(self.labels, p1, p2, p3)
        return p1 + p2 + p3

class Layout2D:

    def __init__(self, x_layout, y_layout):
        self.x = x_layout
        self.y = y_layout

        self.need_x_lim = x_layout.lim is None
        self.need_x_ticks = x_layout.ticks is None
        self.need_y_lim = y_layout.lim is None
        self.need_y_ticks = y_layout.ticks is None

    def fix(self, *, aspect=None):
        if aspect is None:
            self._fix_one("x")
            self._fix_one("y")
            return

        x_unit = self.x.dev_width / _d(self.x.data_range)
        y_unit = self.y.dev_width / _d(self.y.data_range)
        if not self.need_x_lim or (self.need_y_lim and x_unit <= aspect * y_unit):
            self._fix_one("x")
            dy = self.y.dev_width / self.x.dev_width * _d(self.x.lim) * aspect
            self._fix_one("y", constraint=dict(aspect=dy))
        else:
            self._fix_one("y")
            dx = self.x.dev_width / self.y.dev_width * _d(self.y.lim) / aspect
            self._fix_one("x", constraint=dict(aspect=dx))

    def _fix_one(self, axis, constraint=None):
        assert axis in ["x", "y"]
        if axis == "x":
            need_lim = self.need_x_lim
            need_ticks = self.need_x_ticks
            layout = self.x
        else:
            need_lim = self.need_y_lim
            need_ticks = self.need_y_ticks
            layout = self.y

        #  need_lim | need_ticks |
        # ----------+------------+--------------------------------------------
        #  True     | True       | try ticks_within(data) and ticks_over(data),
        #           |            |     compute limits from from ticks
        #  True     | False      | compute limits from from ticks
        #  False    | True       | try ticks_within(limits)
        #  False    | False      | -

        best_penalty = np.inf
        best_ticks = layout.ticks
        best_labels = layout.labels
        best_lim = layout.lim
        if need_lim and need_ticks:
            cand = itertools.chain(
                layout.ticks_within(*layout.data_range, constraint),
                layout.ticks_over(*layout.data_range, constraint))
            for layout.ticks, layout.labels in cand:
                layout.set_limits(constraint)
                penalty = layout.penalty()
                if penalty < best_penalty:
                    best_penalty = penalty
                    best_ticks = layout.ticks
                    best_labels = layout.labels
                    best_lim = layout.lim
        elif need_lim:
            layout.set_limits(constraint)
            best_penalty = layout.penalty()
            best_lim = layout.lim
        elif need_ticks:
            cand = layout.ticks_within(*layout.lim, constraint)
            for layout.ticks, layout.labels in cand:
                penalty = layout.penalty()
                if penalty < best_penalty:
                    best_penalty = penalty
                    best_ticks = layout.ticks
                    best_labels = layout.labels
        else:
            best_penalty = layout.penalty()

        layout.ticks = best_ticks
        layout.labels = best_labels
        layout.lim = best_lim
        return best_penalty

def _d(pair):
    return pair[1] - pair[0]
