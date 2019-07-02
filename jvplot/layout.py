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
            dev_padding (padding): width of padding at both edges, in
                device coordinates.
            data_range (pair): the minimum and maximum data value
                to cover.
            lim (pair, optional): a pair (x0, x1), where x0 is the
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
        dev_pad_l, dev_pad_r = dev_padding

        self.dev_width = dev_width
        self.dev_pad_l = dev_pad_l
        self.dev_pad_r = dev_pad_r
        self.dev_inner = dev_width - dev_pad_l - dev_pad_r
        self.data_range = data_range
        self.lim = lim
        self.ticks = ticks
        self.dev_opt_dist = dev_opt_dist
        self.labels = labels
        self.dev_width_fn = dev_width_fn
        self.can_shift = can_shift
        self.scale = scale

        self.shift = None

    def range_penalty(self):
        penalty = 0
        rel_pad_l = self.dev_pad_l / self.dev_inner
        rel_pad_r = self.dev_pad_r / self.dev_inner

        x0, x1 = self.lim
        left = (self.data_range[0] - x0) / (x1 - x0)
        right = (x1 - self.data_range[1]) / (x1 - x0)
        for val, rel_pad in [(left, rel_pad_l), (right, rel_pad_r)]:
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

        w = self.dev_inner
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

        q = self.dev_inner / (x1 - x0)
        pos = [self.dev_pad_l + (xi - x0)*q for xi in self.ticks]
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

    def data_margins(self):
        """Return the data coordinates of the outer edges of the plot
        (outside the margins).

        """
        a, b = self.lim
        q = (b - a) / self.dev_inner
        return (a - self.dev_pad_l * q, b + self.dev_pad_r * q)

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

        if not self.need_x_lim and not self.need_y_lim:
            raise ValueError("cannot fix aspect ratio and both axes")

        if self.need_y_lim:
            px = self._fix_one("x")
            w = self.y.dev_width / self.x.dev_width * _d(self.x.lim) * aspect
            py = self._fix_one("y", width=w)
            pxy = math.sqrt(px**2 + py**2)
            best_x_ticks = self.x.ticks
            best_x_labels = self.x.labels
            best_x_shift = self.x.shift
            best_x_lim = self.x.lim
            best_y_ticks = self.y.ticks
            best_y_labels = self.y.labels
            best_y_shift = self.y.shift
            best_y_lim = self.y.lim
        else:
            pxy = math.inf

        if self.need_x_lim:
            py = self._fix_one("y")
            w = self.x.dev_width / self.y.dev_width * _d(self.y.lim) / aspect
            px = self._fix_one("x", width=w)
            pyx = math.sqrt(px**2 + py**2)
        else:
            pyx = math.inf

        if pxy < pyx:
            self.x.ticks = best_x_ticks
            self.x.labels = best_x_labels
            self.x.shift = best_x_shift
            self.x.lim = best_x_lim
            self.y.ticks = best_y_ticks
            self.y.labels = best_y_labels
            self.y.shift = best_y_shift
            self.y.lim = best_y_lim


    def _fix_one(self, axis, *, width=None):
        assert axis in ["x", "y"]
        if axis == "x":
            need_lim = self.need_x_lim
            need_ticks = self.need_x_ticks
            layout = self.x
        else:
            need_lim = self.need_y_lim
            need_ticks = self.need_y_ticks
            layout = self.y

        if width is not None and not need_lim:
            raise ValueError("cannot combine fixed limits with fixed width")

        #  need_lim | need_ticks |
        # ----------+------------+--------------------------------------------
        #  True     | True       | try ticks(data),
        #           |            |     compute limits from from ticks
        #  True     | False      | compute limits from from ticks
        #  False    | True       | try ticks(limits, allow_outside=False)
        #  False    | False      | -

        best_penalty = np.inf
        best_ticks = layout.ticks
        best_labels = layout.labels
        best_shift = layout.shift
        best_lim = layout.lim
        if need_lim and need_ticks:
            cand = itertools.islice(
                layout.scale.ticks(*layout.data_range, width=width),
                10)
            for layout.lim, layout.ticks, layout.labels in cand:
                penalty = layout.penalty()
                if penalty < best_penalty:
                    best_penalty = penalty
                    best_ticks = layout.ticks
                    best_labels = layout.labels
                    best_shift = layout.shift
                    best_lim = layout.lim
        elif need_lim:
            a = min(layout.data_range[0], layout.ticks[0])
            b = max(layout.data_range[1], layout.ticks[-1])
            if width is not None:
                layout.lim = ((a + b - width) / 2, (a + b + width) / 2)
            else:
                layout.lim = (a, b)
            best_penalty = layout.penalty()
            best_shift = layout.shift
            best_lim = layout.lim
        elif need_ticks:
            cand = itertools.islice(
                layout.scale.ticks(*layout.lim, allow_outside=False, width=width),
                10)
            for _, layout.ticks, layout.labels in cand:
                penalty = layout.penalty()
                if penalty < best_penalty:
                    best_penalty = penalty
                    best_shift = layout.shift
        else:
            best_penalty = layout.penalty()
            best_shift = layout.shift

        layout.ticks = best_ticks
        layout.labels = best_labels
        layout.shift = best_shift
        layout.lim = best_lim
        return best_penalty

def _d(pair):
    return pair[1] - pair[0]
