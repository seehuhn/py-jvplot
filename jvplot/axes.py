# axes.py - handle coordinate axes
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

"""The Axes class
--------------

The `Axes` class implements all basic drawing operations and allows to
transform between device and data coordinates.

"""

import sys

import numpy as np
import scipy.optimize as opt

import cairocffi as cairo

from . import device
from . import param
from . import util


class Axes(device.Device):

    """A coordinate system on a canvas.

    This class implements coordinate systems on a canvas and,
    optionally, can draw boxes, tick marks, tick labels, and axis
    labels.

    Args:

        parent    The canvas these axes should be drawn on.
        rect      The position of the axes on the parent canvas.
        x_lim     The horizontal range of data coordinates spanned.
        y_lim     The vertical range of data coordinates spanned.

    """

    def __init__(self, parent, rect, x_lim, y_lim, *, style=None):
        # allocate a new drawing context for the viewport
        parent_ctx = parent.ctx
        surface = parent_ctx.get_target()
        ctx = cairo.Context(surface)
        ctx.set_matrix(parent_ctx.get_matrix())
        ctx.rectangle(*rect)
        ctx.clip()

        super().__init__(ctx, rect, res=parent.res, parent=parent, style=style)

        self.parent_ctx = parent_ctx
        self.x_range = x_lim
        self.y_range = y_lim

        # The horizontal scale and offset are determined by the
        # following two equations:
        #     x_lim[0] * x_scale + x_offset = x
        #     x_lim[1] * x_scale + x_offset = x + w
        x_scale = self.rect[2] / (x_lim[1] - x_lim[0])
        x_offset = self.rect[0] - x_lim[0] * x_scale
        # The vertical coordinates are similar:
        y_scale = self.rect[3] / (y_lim[1] - y_lim[0])
        y_offset = self.rect[1] - y_lim[0] * y_scale
        self.offset = (x_offset, y_offset)
        self.scale = (x_scale, y_scale)

    def decorate(self, *, style=None):
        style = param.check_keys(style)

        col = self._get_param('axis_border_col', style)
        border = self._get_param('axis_border_lw', style)

        ctx = self.parent_ctx
        if border > 0 and col[3] > 0:
            ctx.rectangle(*self.rect)
            ctx.set_line_width(border)
            ctx.set_source_rgba(*col)
            ctx.set_line_join(cairo.LINE_JOIN_MITER)
            ctx.stroke()

    def _draw_ticks(self, values, labels, where, style):
        tick_width = self._get_param('axis_tick_width', style)
        tick_length = self._get_param('axis_tick_length', style)
        tick_font_size = self._get_param('tick_font_size', style)
        tick_label_col = self._get_param('tick_font_col', style)
        tick_line_col = self._get_param('axis_tick_col', style)
        x_label_dist = self._get_param('tick_label_dist_x', style)
        y_label_dist = self._get_param('tick_label_dist_y', style)

        w_tab = {
            'b': (False, False, self.rect[1]),
            'l': (True, False, self.rect[0]),
            'r': (True, True, self.rect[0] + self.rect[2]),
            't': (False, True, self.rect[1] + self.rect[3]),
        }
        vertical, rev, pos = w_tab[where]

        if vertical:
            base = np.array([pos, self.offset[1]])
            delta = np.array([0, self.scale[1]])
            d_tick = np.array([tick_length, 0])
            h_align = "left" if rev else "right"
            v_align = "center"
            q = 1 + y_label_dist / tick_length
        else:
            base = np.array([self.offset[0], pos])
            delta = np.array([self.scale[0], 0])
            d_tick = np.array([0, tick_length])
            h_align = "center"
            v_align = "bottom" if rev else "top"
            q = 1 + x_label_dist / tick_length
        if rev:
            d_tick = -d_tick

        adjust = [0] * len(values)
        if labels and not vertical:
            xx = [(base + val * delta)[0] for val in values]
            ww = [self.text_width(lab, tick_font_size) for lab in labels]
            sep = self.text_width("m", tick_font_size)
            qq = _shift_labels(self.rect[0], xx, self.rect[0]+self.rect[2], ww,
                               sep)
            adjust = (qq - .5) * ww

        ctx = self.parent_ctx
        ctx.save()
        self.ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        self.ctx.set_line_width(tick_width)
        self.ctx.set_source_rgba(*tick_line_col)
        for i, val in enumerate(values):
            mid = base + val * delta
            x0, y0 = mid + d_tick
            x1, y1 = mid - d_tick
            ctx.move_to(x0, y0)
            ctx.line_to(x1, y1)

            if labels:
                xt, yt = mid - q*d_tick
                xt -= adjust[i]
                self._draw_text(xt, yt, labels[i], tick_font_size,
                                horizontal_align=h_align,
                                col=tick_label_col,
                                vertical_align=v_align, ctx=ctx)
        ctx.stroke()
        ctx.restore()

    def _draw_axis_label(self, text, where, style):
        dx = self._get_param('axis_label_dist_x', style)
        dy = self._get_param('axis_label_dist_y', style)
        label_font_size = self._get_param('axis_label_size', style)
        label_font_col = self._get_param('axis_label_col', style)

        rect = self.rect
        w_tab = {
            'b': (rect[0] + rect[2]/2, rect[1] - dx,
                  "top", 0),
            't': (rect[0] + rect[2]/2, rect[1] + rect[3] + dx,
                  "bottom", 0),
            'l': (rect[0] - dy, rect[1] + rect[3]/2,
                  "bottom", np.pi/2),
            'r': (rect[0] + rect[2] + dy, rect[1] + rect[3]/2,
                  "top", np.pi/2),
        }
        x, y, align, rot = w_tab[where]

        ctx = self.parent_ctx   # special context to avoid clipping
        ctx.save()
        self._draw_text(x, y, text, label_font_size, col=label_font_col,
                        horizontal_align="center", vertical_align=align,
                        rotate=rot, ctx=ctx)
        ctx.restore()

    def data_to_dev_x(self, x_data):
        return self.offset[0] + x_data * self.scale[0]

    def data_to_dev_y(self, y_data):
        return self.offset[1] + y_data * self.scale[1]

    def draw_lines(self, x, y=None, *, style=None):
        """Draw polygonal line segments.

        The given vertices are connected by a chain of line segments.
        Vertices where at least one of the coordinates is ``nan`` are
        ignored and the line is interupted where such vertices occur.

        Args:
            x (array with ``shape=(n,)`` or ``shape=(n,2)``): The
                vertex coordinates of the line segments.  If `y` is
                given, `x` must be one-dimensional and the vertices
                are ``(x[0], y[0])``, ..., ``(x[n-1], y[n-1])``.
                Otherwise, `x` must be two-dimensional with two
                columns and the vertices are ``x[0,:]``, ...,
                ``x[n-1,:]``.
            y (array with ``shape=(n,)``, optional): See the
                description of `x`.
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        style = param.check_keys(style)
        lw = self._get_param('plot_lw', style)
        col = self._get_param('plot_col', style)

        x, y = util._check_coords(x, y)
        x = self.offset[0] + self.scale[0] * x
        y = self.offset[1] + self.scale[1] * y

        self.ctx.save()
        self.ctx.set_line_width(lw)
        self.ctx.set_source_rgba(*col)
        nan = np.logical_or(np.isnan(x), np.isnan(y)).nonzero()[0]
        nan = [-1] + list(nan) + [len(x)]
        for j in range(1, len(nan)):
            i0 = nan[j-1] + 1
            i1 = nan[j]
            if i0 >= i1:
                continue
            self.ctx.move_to(x[i0], y[i0])
            if i1 == i0+1:
                # only one vertex, so draw a point instead of a line
                self.ctx.line_to(x[i0], y[i0])
                continue
            for i in range(i0+1, i1):
                self.ctx.line_to(x[i], y[i])
        self.ctx.stroke()
        self.ctx.restore()

    def _draw_band(self, x, y_lower, y_mid, y_upper, style):
        bg = self._get_param('band_bg', style)

        xt = self.offset[0] + self.scale[0] * x
        yt_lower = self.offset[1] + self.scale[1] * y_lower
        yt_upper = self.offset[1] + self.scale[1] * y_upper

        if bg[3] > 0:
            self.ctx.save()
            self.ctx.set_source_rgba(*bg)
            op = self.ctx.move_to
            for xi, yi in zip(xt, yt_lower):
                op(xi, yi)
                op = self.ctx.line_to
            for xi, yi in list(zip(xt, yt_upper))[::-1]:
                op(xi, yi)
            self.ctx.fill()
            self.ctx.restore()

        self.draw_lines(x, y_lower)
        if y_mid is not None:
            self.draw_lines(x, y_mid)
        self.draw_lines(x, y_upper)

    def draw_points(self, x, y=None, *, style=None):
        """
        Args:
            x ():
            y ():
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        style = param.check_keys(style)
        lw = self._get_param('plot_point_size', style)
        col = self._get_param('plot_point_col', style)
        separate = self._get_param('plot_point_separate', style)

        x, y = util._check_coords(x, y)
        x = self.offset[0] + self.scale[0] * x
        y = self.offset[1] + self.scale[1] * y

        self.ctx.save()
        self.ctx.set_line_width(lw)
        self.ctx.set_source_rgba(*col)
        if separate:
            for i in range(len(x)):
                self.ctx.move_to(x[i], y[i])
                self.ctx.close_path()
                self.ctx.stroke()
        else:
            for i in range(len(x)):
                self.ctx.move_to(x[i], y[i])
                self.ctx.close_path()
            self.ctx.stroke()
        self.ctx.restore()

    def draw_text(self, text, x, y=None, *, horizontal_align="start",
                  vertical_align="baseline", rotate=0, rotate_deg=None,
                  padding=["1pt", "3pt"], style=None):
        """Add text to a canvas.

        Args:
            text (str): The text to add to the canvas.
            x: Horizontal position of the text in data coordinates.
            y: Vertical position of the text in data coordinates.
            horizontal_align ("start", "end", "left", "right", "center" or dimension):
                Specifies which part of the text to horizontally align
                at the given `x` coordinate.
            vertical_align ("baseline", "top", "bottom", "center" or dimension):
                Specifies which part of the text to vertically align
                at the given `y` coordinate.
            rotate:
            rotate_deg:
            padding:
            style:

        """
        style = param.check_keys(style)
        font_size = self._get_param('text_font_size', style)
        col = self._get_param('text_col', style)
        bg = self._get_param('text_bg', style)

        x, y = util._check_coord_pair(x, y)
        x = self.offset[0] + self.scale[0] * x
        y = self.offset[1] + self.scale[1] * y

        if rotate_deg is not None:
            rotate = float(rotate_deg) / 180 * np.pi

        self._draw_text(x, y, text, font_size, col=col, bg_col=bg,
                        horizontal_align=horizontal_align,
                        vertical_align=vertical_align, rotate=rotate,
                        padding=padding)

    def draw_histogram(self, hist, bin_edges, *, style=None):
        """
        Args:
            hist (array): the data to plot.
            bin_edges (array): a vector of bin edges.
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        style = param.check_keys(style)
        lc = self._get_param('hist_col', style)
        lw = self._get_param('hist_lw', style)
        fc = self._get_param('hist_fill_col', style)

        x = self.offset[0] + self.scale[0] * bin_edges
        y = self.offset[1] + self.scale[1] * hist

        self.ctx.save()
        for i, yi in enumerate(y):
            x0 = x[i]
            x1 = x[i+1]
            self.ctx.rectangle(x0, self.offset[1],
                               x1 - x0, yi - self.offset[1])
        if fc is not None:
            self.ctx.set_source_rgba(*fc)
            self.ctx.fill_preserve()
        if lw and lc is not None:
            max_bin_width = np.amax(x[1:] - x[:-1])
            if lw > .25 * max_bin_width:
                lw = .25 * max_bin_width
            self.ctx.set_line_width(lw)
            self.ctx.set_source_rgba(*lc)
            self.ctx.stroke()
        self.ctx.restore()

    def draw_affine(self, *, x=None, y=None, a=None, b=None, style=None):
        """Draw a straight line.

        Args:
            x (number): if `x` is not ``None``, draw a vertical line at
                horizontal position `x` (in data coordinates).
            y (number): if `y` is not ``None``, draw a horizontal line at
                vertical position `y` (in data coordinates).
            a (number): if `a` and `b` are not ``None``, draw the
                affine function :math:`a + bx` (in data coordinates).
            b (number): see `a`.
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """

        style = param.check_keys(style)
        lw = self._get_param('affine_lw', style)
        col = self._get_param('affine_line_col', style)
        dash = self._get_param('line_dash', style)

        if x is not None:
            x = float(x)
            assert y is None and a is None and b is None
            x = self.offset[0] + x * self.scale[0]
            self.ctx.save()
            self.ctx.set_line_width(lw)
            self.ctx.set_source_rgba(*col)
            self.ctx.set_dash(dash)
            self.ctx.move_to(x, self.rect[1])
            self.ctx.line_to(x, self.rect[1] + self.rect[3])
            self.ctx.stroke()
            self.ctx.restore()
            return

        if y is not None:
            assert x is None and a is None and b is None
            a = float(y)
            b = 0.0
        else:
            a = float(a)
            b = float(b)

        # self._orig_x = self.offset[0] + x0 * self.scale[0]
        x0 = (self.rect[0] - self.offset[0]) / self.scale[0]
        y0 = a + b * x0
        # self._orig_x + self._orig_width = self.offset[0] + x1 * self.scale[0]
        x1 = (self.rect[0] + self.rect[2] - self.offset[0]) / self.scale[0]
        y1 = a + b * x1

        self.ctx.save()
        self.ctx.set_line_width(lw)
        self.ctx.set_source_rgba(*col)
        self.ctx.set_dash(dash)
        self.ctx.move_to(self.rect[0],
                         self.offset[1] + y0 * self.scale[1])
        self.ctx.line_to(self.rect[0] + self.rect[2],
                         self.offset[1] + y1 * self.scale[1])
        self.ctx.stroke()
        self.ctx.restore()

    def draw_image(self, pixels, x_range=None, y_range=None, *, style=None):
        """Draw a raster image onto the canvas.

        The array ``pixels`` gives the pixel intensities, as RGB
        intensities in the range [0, 1].  The array must have the
        shape ``pix_height x pix_width x 3``, where the last
        coordinate indicates the colour channels in the order red,
        green, blue.

        args:
            pixels (array): the pixel intensities, in the form described
                above.
            ...
            style (dict, optional): Default plot graphics values for the
                canvas.

        """
        style = param.check_keys(style)
        if x_range is None:
            x_range = self.x_range
        if y_range is None:
            y_range = self.y_range

        pixels = np.array(pixels)
        s = pixels.shape
        if len(s) != 3 or s[2] != 3:
            raise ValueError("image data must have have shape h x w x 3")
        if np.min(pixels) < 0 or np.max(pixels) > 1:
            raise ValueError("image intensities must be in the range [0, 1]")
        pix_h, pix_w = s[:2]

        # prepare a bytearray to hold the image data
        buf = bytearray(pix_w * pix_h * 4)
        sur_img = cairo.ImageSurface(cairo.FORMAT_RGB24, pix_w, pix_h, buf)

        # write the image data into the bytearray
        img = np.asarray(buf).reshape((pix_h, pix_w, 4))
        if sys.byteorder == "little":
            # bring the channels into ARGB order:
            img = img[:, :, ::-1]
        np.clip(pixels*256, 0, 255, out=img[:, :, 1:])

        x0 = self.data_to_dev_x(x_range[0])
        x1 = self.data_to_dev_x(x_range[1])
        y0 = self.data_to_dev_y(y_range[0])
        y1 = self.data_to_dev_y(y_range[1])

        # copy the source image onto the Axes surface
        self.ctx.save()
        self.ctx.translate(x0, y0)
        self.ctx.scale((x1-x0)/pix_w, (y1-y0)/pix_h)
        self.ctx.set_source_surface(sur_img, 0, 0)
        self.ctx.get_source().set_filter(cairo.FILTER_NEAREST)
        self.ctx.rectangle(0, 0, pix_w, pix_h)
        self.ctx.fill()

        self.ctx.restore()
        sur_img.finish()

def _shift_labels(left, xx, right, ww, sep=10):
    xx = np.array(xx)
    ww = np.array(ww)

    def loss(qq):
        l = xx - qq*ww
        r = xx + (1-qq)*ww
        a = np.sum(np.square(np.maximum(r[:-1] - l[1:] + sep, 0)))
        b = np.sum(np.square(np.maximum([left - l[0], r[-1] - right], 0)))
        c = np.sum(np.square(qq - .5))
        return a + .1*b + .01*c

    n = len(xx)
    res = opt.minimize(loss, [.5]*n, bounds=[(0, 1)]*n, method='L-BFGS-B')
    return res.x
