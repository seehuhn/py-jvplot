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

from .util import _convert_dim
from .util import _check_coords, _check_num_vec, _check_range, _check_vec
from .param import get

def _prepare_context(ctx):
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)

def _scales(x):
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

def _steps(a, b, scale):
    step_a = int(np.ceil(a / scale - 0.001))
    step_b = int(np.ceil(b / scale + 0.001))
    return list(np.arange(step_a, step_b) * scale)

def _improve_range(r):
    a, b = r
    for scale in _scales(b-a):
        if b - a > 10 * scale:
            break
        a2 = np.floor(a / scale) * scale
        b2 = np.ceil(b / scale) * scale
        if b2 - a2 < 1.2 * (b - a):
            return (a2, b2)
    return r

class Canvas:
    """The Canvas class."""

    def __init__(self, ctx, x, y, w, h, res, style={}):
        """Allocate a new canvas."""
        self.ctx = ctx
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.res = res
        self.style = dict(style)

        self.offset = None
        self.scale = None
        self.axes = None

    def __str__(self):
        return "<Canvas %.0fx%.0f%+.0f%+.0f>" % (self.w, self.h, self.x, self.y)

    def _set_defaults(self, style):
        res = dict(self.style)
        res.update(style)
        return res

    def set_range(self, x_range, y_range, aspect=None, smart=True):
        """Set the transformation from data to canvas coordinates.  This
        method must be called before any data can be plotted onto the
        canvas.

        Arguments:

        x_range
            A pair of numbers, giving the minimal/maximal x-coordinate
            of the data.
        y_range
            A pair of numbers, giving the minimal/maximal y-coordinate
            of the data.
        aspect
            If not `None`, a number describing the ratio between
            vertical and horizontal scale.  If `aspect > 1`, a circle
            in data-space will appear higher than wide on the canvas.

        """
        x_range = _check_range(x_range)
        y_range = _check_range(y_range)

        sx = self.w / (x_range[1] - x_range[0])
        sy = self.h / (y_range[1] - y_range[0])
        if smart and aspect is None and sx < 1.1*sy and sy < 1.1*sx:
            aspect = 1
        if aspect is not None:
            if sx * aspect > sy:
                # we want aspect * sx == sy, so we have to widen x_range
                x_width = aspect * self.w / sy
                x_inc = x_width - (x_range[1] - x_range[0])
                x_range = (x_range[0] - .5*x_inc, x_range[1] + .5*x_inc)
            else:
                # we want aspect * sx == sy, so we have to widen y_range
                y_width = self.h / aspect / sx
                y_inc = y_width - (y_range[1] - y_range[0])
                y_range = (y_range[0] - .5*y_inc, y_range[1] + .5*y_inc)

        # The horizontal scale and offset are determined by the
        # following two equations:
        #     x_range[0] * x_scale + x_offset = x
        #     x_range[1] * x_scale + x_offset = x + w
        x_scale = self.w / (x_range[1] - x_range[0])
        x_offset = self.x - x_range[0] * x_scale
        # The vertical coordinates are similar:
        y_scale = self.h / (y_range[1] - y_range[0])
        y_offset = self.y - y_range[0] * y_scale
        self.offset = (x_offset, y_offset)
        self.scale = (x_scale, y_scale)
        return x_range, y_range

    def add_padding(self, padding):
        """Add extra padding around the edge of the canvas."""
        padding = _check_vec(padding, 4, True)
        p_top = _convert_dim(padding[0], self.res, self.h)
        p_right = _convert_dim(padding[1], self.res, self.w)
        p_bottom = _convert_dim(padding[2], self.res, self.h)
        p_left = _convert_dim(padding[3], self.res, self.w)
        self.x += p_left
        self.w -= p_left + p_right
        self.y += p_bottom
        self.h -= p_bottom + p_top

    def get_viewport(self, width=None, height=None, margin=None, border=0,
                     padding=0, style={}):
        """Get a new canvas representing a rectangular sub-region of the
        current canvas.

        """
        width = _convert_dim(width, self.res, self.w, allow_none=True)
        height = _convert_dim(height, self.res, self.h, allow_none=True)

        margin = _check_vec(margin, 4, True)
        m_top = _convert_dim(margin[0], self.res, self.h, allow_none=True)
        m_right = _convert_dim(margin[1], self.res, self.w, allow_none=True)
        m_bottom = _convert_dim(margin[2], self.res, self.h, allow_none=True)
        m_left = _convert_dim(margin[3], self.res, self.w, allow_none=True)

        if isinstance(border, str):
            border = border.split()
            border_width = border[0]
        else:
            border_width = border
        border_width = _convert_dim(border_width, self.res)
        if border_width < 0:
            raise ValueError('negative border width in "%s"' % border)

        padding = _check_vec(padding, 4, True)
        p_top = _convert_dim(padding[0], self.res, self.h)
        p_right = _convert_dim(padding[1], self.res, self.w)
        p_bottom = _convert_dim(padding[2], self.res, self.h)
        p_left = _convert_dim(padding[3], self.res, self.w)

        total_w = sum(x for x in [m_left, border_width, p_left, width,
                                  p_right, border_width, m_right]
                      if x is not None)
        if total_w > self.w:
            raise ValueError("total width %f > %f" % (total_w, self.w))
        if width is None:
            width = self.w - total_w
        spare_w = self.w - 2*border_width - p_left - width - p_right
        if m_left is None and m_right is None:
            m_left = max(spare_w / 2, 0)
        elif m_left is None:
            m_left = spare_w - m_right

        total_h = sum(x for x in [m_bottom, border_width, p_bottom, height,
                                  p_top, border_width, m_top]
                      if x is not None)
        if total_h > self.h:
            raise ValueError("total height %f > %f" % (total_h, self.h))
        if height is None:
            height = self.h - total_h
        spare_h = self.h - 2*border_width - p_bottom - height - p_top
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

        res = Canvas(ctx, x, y, w, h, self.res, style=self._set_defaults(style))
        res.add_padding([p_top / self.res, p_right / self.res,
                         p_bottom / self.res, p_left / self.res])
        return res, border_rect

    def subplot(self, cols, rows, idx, padding=0, style={}):
        if rows <= 0 or cols <= 0:
            return ValueError('invalid %d by %d arrangement' % (cols, rows))
        if not 0 <= idx < cols*rows:
            tmpl = 'invalid index %d, not in range 0, ... %d'
            raise ValueError(tmpl % (idx, cols*rows-1))
        i = idx // cols
        j = idx % cols
        dw = self.w / cols / self.res
        dh = self.h / rows / self.res
        return self.get_viewport(width=dw, height=dh,
                                 margin=[i*dh, None, None, j*dw],
                                 padding=padding)

    def get_axes(self, x_range, y_range, aspect=None, smart=True, width=None,
                 height=None, margin=None, border=None, padding=None, style={}):
        """Draw a set of coordinate axes and return a new canvas representing
        the data area inside the axes.

        """
        if margin is None:
            margin = ["2mm", "2mm", "7mm", "14mm"]
        if border is None:
            border = "1pt"
        if padding is None:
            padding = "2mm"
        axes, rect = self.get_viewport(width, height, margin, border, padding,
                                       style=style)

        if smart:
            x_range = _improve_range(x_range)
            y_range = _improve_range(y_range)
        x_range, y_range = axes.set_range(x_range, y_range, aspect=aspect)

        style = self._set_defaults(style)

        tick_width = get('axis_tick_width', self.res, style)
        tick_length = get('axis_tick_length', self.res, style)
        font_size = get('axis_font_size', self.res, style)

        self.ctx.save()
        self.ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        self.ctx.set_font_matrix(
            cairo.Matrix(font_size, 0, 0, -font_size, 0, 0))
        self.ctx.set_line_width(tick_width)

        ascent, descent, _, _, _ = self.ctx.font_extents()

        opt_spacing = min(axes.w / 4,
                          get('axis_tick_opt_spacing', axes.res, style))
        best_score = None
        for scale in _scales(x_range[1] - x_range[0]):
            steps = _steps(x_range[0], x_range[1], scale)

            labels = ["%g" % x for x in steps]
            exts = [self.ctx.text_extents(x) for x in labels]

            spacing = axes.scale[0] * scale
            if max(e[4] for e in exts) >= spacing and best_score is not None:
                break
            score = np.abs(np.log(spacing / opt_spacing))
            if best_score is None or score < best_score:
                best_score = score
                best_spacing = spacing
                best_steps = steps
                best_labels = labels
                best_exts = exts
        x_label_dist = get('axis_x_label_dist', self.res, style)
        for step, label, ext in zip(best_steps, best_labels, best_exts):
            x = axes.offset[0] + axes.scale[0] * step
            self.ctx.move_to(x, rect[1] - tick_length)
            self.ctx.line_to(x, rect[1] + tick_length)
            self.ctx.move_to(x - .5 * ext[4],
                             rect[1] - .5 * tick_length - x_label_dist - ascent)
            self.ctx.show_text(label)

        opt_spacing = best_spacing
        best_score = None
        for scale in _scales(y_range[1] - y_range[0]):
            steps = _steps(y_range[0], y_range[1], scale)

            labels = ["%g" % x for x in steps]
            exts = [self.ctx.text_extents(x) for x in labels]

            spacing = axes.scale[1]*scale
            if max(e[3] for e in exts) >= spacing and best_score is not None:
                break
            score = np.abs(np.log(spacing / opt_spacing))
            if best_score is None or score < best_score:
                best_score = score
                best_spacing = spacing
                best_steps = steps
                best_labels = labels
                best_exts = exts
        y_label_dist = get('axis_y_label_dist', self.res, style)
        for step, label, ext in zip(best_steps, best_labels, best_exts):
            y = axes.offset[1] + axes.scale[1] * step
            self.ctx.move_to(rect[0] - tick_length, y)
            self.ctx.line_to(rect[0] + tick_length, y)
            self.ctx.move_to(rect[0] - tick_length - y_label_dist - ext[4],
                             y - .5*(ascent - descent))
            self.ctx.show_text(label)
        self.ctx.stroke()
        self.ctx.restore()

        return axes

    def _make_line_shape(self, x, y):
        x = self.offset[0] + self.scale[0] * x
        y = self.offset[1] + self.scale[1] * y
        self.ctx.move_to(x[0], y[0])
        for i in range(1, len(x)):
            self.ctx.line_to(x[i], y[i])

    def _make_dot_shape(self, x, y):
        x = self.offset[0] + self.scale[0] * x
        y = self.offset[1] + self.scale[1] * y
        for i in range(len(x)):
            self.ctx.move_to(x[i], y[i])
            self.ctx.close_path()

    def plot(self, x, y=None, aspect=None,
             smart=True, width=None, height=None, margin=None,
             border=None, padding=None, style={}):
        """Draw a line plot."""
        x, y = _check_coords(x, y)
        xmin = np.amin(x)
        xmax = np.amax(x)
        ymin = np.amin(y)
        ymax = np.amax(y)
        axes = self.get_axes((xmin, xmax), (ymin, ymax), aspect=aspect,
                             smart=smart, width=width, height=height,
                             margin=margin, border=border, padding=padding,
                             style=style)

        style = axes._set_defaults(style)

        axes.ctx.save()
        lw = get('plot_lw', axes.res, style)
        axes.ctx.set_line_width(lw)
        axes._make_line_shape(x, y)
        axes.ctx.stroke()
        axes.ctx.restore()

        return axes

    def scatter_plot(self, x, y=None, size=None, aspect=None,
                     smart=True, width=None, height=None, margin=None,
                     border=None, padding=None, style={}):
        """Draw a scatter plot."""
        x, y = _check_coords(x, y)
        xmin = np.amin(x)
        xmax = np.amax(x)
        ymin = np.amin(y)
        ymax = np.amax(y)
        axes = self.get_axes((xmin, xmax), (ymin, ymax), aspect=aspect,
                             smart=smart, width=width, height=height,
                             margin=margin, border=border, padding=padding,
                             style=style)
        axes._make_dot_shape(x, y)
        axes.ctx.stroke()
        return axes
