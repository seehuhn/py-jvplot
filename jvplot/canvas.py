# canvas.py - implementation of the Canvas class
# Copyright (C) 2014 Jochen Voss <voss@seehuhn.de>
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

"""The Canvas class
----------------

The canvas class implements all drawing operations supported by the
JvPlot package.

"""

import numpy as np

import cairocffi as cairo

from . import axis
from .util import _convert_dim
from .util import _check_coords, _check_num_vec, _check_range, _check_vec
from .param import get

def _prepare_context(ctx):
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)

def _scales(x):
    "return decreasing scales smaller than x"
    step = int(np.log10(x))
    while True:
        base = 10**step
        if 5 * base < x:
            yield 5 * base
        if 2.5 * base < x:
            yield 2.5 * base
        if 2 * base < x:
            yield 2 * base
        yield base
        step -= 1

def _try_steps(a, b):
    for scale in _scales(b-a):
        step_a = int(np.floor(a / scale + 0.01))
        step_b = int(np.ceil(b / scale - 0.01))
        steps = list(np.arange(step_a, step_b+1) * scale)

        n = len(steps)
        can_drop_left = n > 2 and (steps[1] - a) < .5 * scale
        can_drop_right = n > 2 and (b - steps[-2]) < .5 * scale
        if n > 3 and can_drop_left and can_drop_right:
            yield (a, b), steps[1:-1]
        if n > 2 and can_drop_left:
            yield (a, step_b*scale), steps[1:]
        if n > 2 and can_drop_right:
            yield (step_a*scale, b), steps[:-1]
        if n > 1:
            yield (step_a*scale, step_b*scale), steps

class Canvas:
    """The Canvas class."""

    def __init__(self, ctx, x, y, w, h, res, style={}):
        """Allocate a new canvas."""
        self.ctx = ctx

        self.x = x
        """Horizontal position of this canvas on the canvas, in device
        coordinate units (read only)."""

        self.y = y
        """Vertical position of this canvas on the canvas, in device
        coordinate units (read only)."""

        self.width = w
        "Width of the canvas in device coordinate units (read only)."

        self.height = h
        "Height of the canvas in device coordinate units (read only)."

        self.res = res
        """Resolution of the canvas, *i.e.* the number of device coordinate
        units per inch (read only)."""

        self.style = dict(style)

        self.offset = None
        self.scale = None
        self.axes = None

    def __str__(self):
        return "<Canvas %.0fx%.0f%+.0f%+.0f>" % (self.width, self.height, self.x, self.y)

    def _merge_defaults(self, style):
        res = dict(self.style)
        res.update(style)
        return res

    def add_padding(self, padding):
        """Add extra padding around the edge of the canvas."""
        padding = _check_vec(padding, 4, True)
        p_top = _convert_dim(padding[0], self.res, self.height)
        p_right = _convert_dim(padding[1], self.res, self.width)
        p_bottom = _convert_dim(padding[2], self.res, self.height)
        p_left = _convert_dim(padding[3], self.res, self.width)
        self.x += p_left
        self.width -= p_left + p_right
        self.y += p_bottom
        self.height -= p_bottom + p_top

    def set_limits(self, x_lim, y_lim):
        """Set the transformation from data to canvas coordinates.  This
        method must be called before any data can be plotted onto the
        canvas.

        Arguments:

        x_lim
            A pair of numbers, giving the minimal/maximal x-coordinate
            of the data.
        y_lim
            A pair of numbers, giving the minimal/maximal y-coordinate
            of the data.

        """
        x_lim = _check_range(x_lim)
        y_lim = _check_range(y_lim)

        # The horizontal scale and offset are determined by the
        # following two equations:
        #     x_lim[0] * x_scale + x_offset = x
        #     x_lim[1] * x_scale + x_offset = x + w
        x_scale = self.width / (x_lim[1] - x_lim[0])
        x_offset = self.x - x_lim[0] * x_scale
        # The vertical coordinates are similar:
        y_scale = self.height / (y_lim[1] - y_lim[0])
        y_offset = self.y - y_lim[0] * y_scale
        self.offset = (x_offset, y_offset)
        self.scale = (x_scale, y_scale)
        return x_lim, y_lim

    def _viewport(self, width, height, margin, border, padding, style):
        width = _convert_dim(width, self.res, self.width, allow_none=True)
        height = _convert_dim(height, self.res, self.height, allow_none=True)

        margin = _check_vec(margin, 4, True)
        m_top = _convert_dim(margin[0], self.res, self.height, allow_none=True)
        m_right = _convert_dim(margin[1], self.res, self.width, allow_none=True)
        m_bottom = _convert_dim(margin[2], self.res, self.height, allow_none=True)
        m_left = _convert_dim(margin[3], self.res, self.width, allow_none=True)

        if isinstance(border, str):
            border = border.split()
            border_width = border[0]
        else:
            border_width = border
        border_width = _convert_dim(border_width, self.res)
        if border_width < 0:
            raise ValueError('negative border width in "%s"' % border)

        padding = _check_vec(padding, 4, True)
        p_top = _convert_dim(padding[0], self.res, self.height)
        p_right = _convert_dim(padding[1], self.res, self.width)
        p_bottom = _convert_dim(padding[2], self.res, self.height)
        p_left = _convert_dim(padding[3], self.res, self.width)

        total_w = sum(x for x in [m_left, border_width, p_left, width,
                                  p_right, border_width, m_right]
                      if x is not None)
        if total_w > self.width:
            raise ValueError("total width %f > %f" % (total_w, self.width))
        if width is None:
            width = self.width - total_w
        spare_w = self.width - 2*border_width - p_left - width - p_right
        if m_left is None and m_right is None:
            m_left = max(spare_w / 2, 0)
        elif m_left is None:
            m_left = spare_w - m_right

        total_h = sum(x for x in [m_bottom, border_width, p_bottom, height,
                                  p_top, border_width, m_top]
                      if x is not None)
        if total_h > self.height:
            raise ValueError("total height %f > %f" % (total_h, self.height))
        if height is None:
            height = self.height - total_h
        spare_h = self.height - 2*border_width - p_bottom - height - p_top
        if m_bottom is None and m_top is None:
            m_bottom = max(spare_h / 2, 0)
        elif m_bottom is None:
            m_bottom = spare_h - m_top

        border_rect = [
            self.x + m_left + 0.5*border_width,
            self.y + m_bottom + 0.5*border_width,
            border_width + p_left + width + p_right,
            border_width + p_bottom + height + p_top
        ]
        if border_width > 0:
            self.ctx.save()
            self.ctx.rectangle(*border_rect)
            self.ctx.set_line_width(border_width)
            self.ctx.set_line_join(cairo.LINE_JOIN_MITER)
            self.ctx.stroke()
            self.ctx.restore()

        # allocate a new drawing context for the viewport
        surface = self.ctx.get_target()
        ctx = cairo.Context(surface)
        ctx.set_matrix(self.ctx.get_matrix())
        _prepare_context(ctx)

        x = self.x + m_left + border_width
        y = self.y + m_bottom + border_width
        w = p_left + width + p_right
        h = p_bottom + height + p_top
        ctx.rectangle(x, y, w, h)
        ctx.clip()

        res = Canvas(ctx, x, y, w, h, self.res, style=self._merge_defaults(style))
        res.add_padding([p_top / self.res, p_right / self.res,
                         p_bottom / self.res, p_left / self.res])
        return res, border_rect

    def viewport(self, width=None, height=None, margin=None, border=0,
                 padding=0, style={}):
        """Get a new canvas representing a rectangular sub-region of the
        current canvas.

        """
        res, _ = self._viewport(width, height, margin, border, padding, style)
        return res

    def subplot(self, cols, rows, idx, padding=0, style={}):
        if rows <= 0 or cols <= 0:
            return ValueError('invalid %d by %d arrangement' % (cols, rows))
        if not 0 <= idx < cols*rows:
            tmpl = 'invalid index %d, not in range 0, ... %d'
            raise ValueError(tmpl % (idx, cols*rows-1))
        i = idx // cols
        j = idx % cols
        dw = self.width / cols / self.res
        dh = self.height / rows / self.res
        return self.viewport(width=dw, height=dh,
                             margin=[i*dh, None, None, j*dw],
                             padding=padding)

    def _layout_labels(self, x_lim, y_lim, aspect, font_ctx):
        opt_spacing = get('axis_tick_opt_spacing', self.res, self.style)

        font_extents = font_ctx.font_extents()
        x_label_sep = get('axis_x_label_sep', self.res, self.style)
        if aspect is None:
            # horizontal axis
            best_p = np.inf
            stop = 3
            for lim, steps in _try_steps(*x_lim):
                if stop < 0:
                    break

                labels = ["%g" % pos for pos in steps]
                p = axis._penalties(self.width, x_lim, lim, steps, labels, True,
                                    font_ctx, x_label_sep,
                                    min(self.width/2, opt_spacing))
                ps = np.array([1.0, 1.0, 1.0, 1.0]).dot(p)
                if ps < best_p:
                    best_p = ps
                    best_xlim = lim
                    best_xsteps = steps
                    best_xlabels = labels
                else:
                    stop -= 1

            # vertical axis
            best_p = np.inf
            stop = 3
            for lim, steps in _try_steps(*y_lim):
                if stop < 0:
                    break

                labels = ["%g" % pos for pos in steps]
                p = axis._penalties(self.height, y_lim, lim, steps, labels, False,
                                    font_ctx, 0.0, min(self.height/2, opt_spacing))
                ps = np.array([1.0, 1.0, 1.0, 1.0]).dot(p)
                if ps < best_p:
                    best_p = ps
                    best_ylim = lim
                    best_ysteps = steps
                    best_ylabels = labels
                else:
                    stop -= 1
        else:                   # aspect ratio is set
            q = aspect * self.width / self.height
            x_range = max(x_lim[1] - x_lim[0], (y_lim[1] - y_lim[0]) * q)
            x_start = axis._next_scale(x_range)
            y_range = max(y_lim[1] - y_lim[0], (x_lim[1] - x_lim[0]) / q)
            y_start = axis._next_scale(y_range)

            best_p = np.inf
            for data in axis._try_pairs(x_lim, x_start, y_lim, y_start, q):
                x_axis_lim, x_ticks, y_axis_lim, y_ticks = data
                x_labels = ["%g" % pos for pos in x_ticks]
                px = axis._penalties(self.width, x_lim, x_axis_lim, x_ticks,
                                     x_labels, True, font_ctx, x_label_sep,
                                     min(self.width/2, opt_spacing))
                pxs = np.array([1.0, 1.0, 1.0, 1.0]).dot(px)
                y_labels = ["%g" % pos for pos in y_ticks]
                py = axis._penalties(self.height, y_lim, y_axis_lim, y_ticks,
                                     y_labels, False, font_ctx, 0,
                                     min(self.height/2, opt_spacing))
                pys = np.array([1.0, 1.0, 1.0, 1.0]).dot(py)
                ps = pxs + pys

                if ps < best_p:
                    best_p = ps
                    best_xlim = x_axis_lim
                    best_xsteps = x_ticks
                    best_xlabels = x_labels
                    best_ylim = y_axis_lim
                    best_ysteps = y_ticks
                    best_ylabels = y_labels
        return [
            best_xlim, zip(best_xsteps, best_xlabels),
            best_ylim, zip(best_ysteps, best_ylabels),
        ]

    def draw_axes(self, x_lim, y_lim, aspect=None, width=None, height=None,
                  margin=None, border=None, padding=None, style={}):
        """Draw a set of coordinate axes and return a new canvas representing
        the data area inside the axes.

        """
        if margin is None:
            margin = ["2mm", "2mm", "7mm", "14mm"]
        if border is None:
            border = get('axis_lw', self.res, style) / self.res
        if padding is None:
            padding = "2mm"
        axes, rect = self._viewport(width, height, margin, border, padding,
                                    style)

        tick_width = get('axis_tick_width', self.res, axes.style)
        tick_length = get('axis_tick_length', self.res, axes.style)
        font_size = get('axis_font_size', self.res, axes.style)
        self.ctx.save()
        self.ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        self.ctx.set_font_matrix(
            cairo.Matrix(font_size, 0, 0, -font_size, 0, 0))
        self.ctx.set_line_width(tick_width)

        x_lim, x_labels, y_lim, y_labels = axes._layout_labels(
            x_lim, y_lim, aspect, self.ctx)
        axes.set_limits(x_lim, y_lim)
        ascent, descent, _, _, _ = self.ctx.font_extents()
        x_label_dist = get('axis_x_label_dist', self.res, style)
        for x_pos, x_lab in x_labels:
            x_pos = axes.offset[0] + x_pos * axes.scale[0]
            ext = self.ctx.text_extents(x_lab)
            self.ctx.move_to(x_pos, rect[1] - tick_length)
            self.ctx.line_to(x_pos, rect[1] + tick_length)
            self.ctx.move_to(x_pos - .5 * ext[4],
                             rect[1] - .5 * tick_length - x_label_dist - ascent)
            self.ctx.show_text(x_lab)
        y_label_dist = get('axis_y_label_dist', self.res, style)
        for y_pos, y_lab in y_labels:
            y_pos = axes.offset[1] + y_pos * axes.scale[1]
            ext = self.ctx.text_extents(y_lab)
            self.ctx.move_to(rect[0] - tick_length, y_pos)
            self.ctx.line_to(rect[0] + tick_length, y_pos)
            self.ctx.move_to(rect[0] - tick_length - y_label_dist - ext[4],
                             y_pos - .5*(ascent - descent))
            self.ctx.show_text(y_lab)
        self.ctx.stroke()
        self.ctx.restore()

        self.axes = axes
        return axes

    def draw_lines(self, x, y=None, style={}):
        x, y = _check_coords(x, y)
        x = self.offset[0] + self.scale[0] * x
        y = self.offset[1] + self.scale[1] * y
        style = self._merge_defaults(style)

        self.ctx.save()
        lw = get('plot_lw', self.res, style)
        self.ctx.set_line_width(lw)
        self.ctx.move_to(x[0], y[0])
        for i in range(1, len(x)):
            self.ctx.line_to(x[i], y[i])
        self.ctx.stroke()
        self.ctx.restore()

    def plot(self, x, y=None, aspect=None, width=None, height=None,
             margin=None, border=None, padding=None, style={}):
        """Draw a line plot."""
        x, y = _check_coords(x, y)
        if self.axes is None:
            xmin = np.amin(x)
            xmax = np.amax(x)
            ymin = np.amin(y)
            ymax = np.amax(y)
            self.draw_axes(
                (xmin, xmax), (ymin, ymax), aspect=aspect, width=width,
                height=height, margin=margin, border=border, padding=padding,
                style=style)
        self.axes.draw_lines(x, y, style=style)
        return self.axes

    def draw_points(self, x, y=None, style={}):
        x, y = _check_coords(x, y)
        x = self.offset[0] + self.scale[0] * x
        y = self.offset[1] + self.scale[1] * y
        style = self._merge_defaults(style)

        self.ctx.save()
        lw = get('plot_point_size', self.res, style)
        self.ctx.set_line_width(lw)
        for i in range(len(x)):
            self.ctx.move_to(x[i], y[i])
            self.ctx.close_path()
        self.ctx.stroke()
        self.ctx.restore()

    def scatter_plot(self, x, y=None, aspect=None, width=None,
                     height=None, margin=None, border=None, padding=None,
                     style={}):
        """Draw a scatter plot."""
        x, y = _check_coords(x, y)
        if self.axes is None:
            xmin = np.amin(x)
            xmax = np.amax(x)
            ymin = np.amin(y)
            ymax = np.amax(y)
            self.draw_axes(
                (xmin, xmax), (ymin, ymax), aspect=aspect, width=width,
                height=height, margin=margin, border=border, padding=padding,
                style=style)
        self.axes.draw_points(x, y)
        return self.axes

    def draw_histogram(self, hist, bin_edges, style={}):
        x = self.offset[0] + self.scale[0] * bin_edges
        y = self.offset[1] + self.scale[1] * hist
        self.ctx.save()
        lw = get('hist_lw', self.res, style)
        self.ctx.set_line_width(lw)
        for i, yi in enumerate(y):
            x0 = x[i]
            x1 = x[i+1]
            self.ctx.rectangle(x0, 0, x1 - x0, yi)
        self.ctx.stroke()
        self.ctx.restore()

    def histogram(self, x, bins=10, range=None, weights=None, density=False,
                  width=None, height=None, margin=None, border=None,
                  padding=None, style={}):
        """Draw a histogram."""
        hist, bin_edges = np.histogram(x, bins=bins, range=range,
                                       weights=weights, density=density)
        if self.axes is None:
            xmin = np.amin(bin_edges)
            xmax = np.amax(bin_edges)
            ymin = 0
            ymax = np.amax(hist)
            self.draw_axes(
                (xmin, xmax), (ymin, ymax), width=width,
                height=height, margin=margin, border=border, padding=padding,
                style=style)
        self.axes.draw_histogram(hist, bin_edges, style)
        return self.axes
