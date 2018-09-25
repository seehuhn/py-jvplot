# canvas.py - implementation of the Canvas class
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

"""The Canvas class
----------------

The canvas class implements all drawing operations supported by the
JvPlot package.

"""

import sys

import numpy as np

import cairocffi as cairo

from . import color
from . import coords
from . import errors
from . import param
from . import util


class Device:

    """A graphics device to draw a plot on.

    This class is only used as a base class for :py:class:`Canvas` and
    :py:class:`Axes`.  The ``Device`` class itself is not normally
    instantiated.

    This class keeps track of the resolution and dimensions of the
    drawing area, and of the graphical style parameters.

    """

    def __init__(self, ctx, rect, *, res, style=None, parent=None):
        if parent is None:
            style = param.update(param.ROOT, style)
        else:
            style = param.update(style, parent_style=parent.style)
        self.style = style

        if ctx is not None:
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.ctx = ctx

        self.res = res
        """Device resolution, *i.e.* the number of coordinate units per inch
        (read only).

        """

        self.rect = rect
        """The extent of the drawing area, in device coordinates (Read only).

        The four values `x, y, w, h = rect` represent the horizontal
        and vertical position of the drawing area on the page, and the
        width and hight of the drawing area, respectively.

        """

    def _get_param(self, key, style):
        keys = [key]
        while True:
            value = style.get(key)
            if value is None:
                value = self.style.get(key)
            if value is None:
                msg = f"invalid style parameter '{key}'"
                raise errors.InvalidParameterName(msg)

            if isinstance(value, str) and value.startswith('$'):
                key = value[1:]
                if key in keys:
                    msg = ' -> '.join(keys + [key])
                    raise errors.WrongUsage("infinite parameter loop: " + msg)
                keys.append(key)
            else:
                break

        info = param.DEFAULT[key]
        if info[0] == 'width':
            return util.convert_dim(value, self.res, self.rect[2])
        if info[0] == 'height':
            return util.convert_dim(value, self.res, self.rect[3])
        if info[0] == 'dim':
            return util.convert_dim(value, self.res)
        if info[0] == 'col':
            return color.get(value)
        if info[0] == 'bool':
            return bool(value)
        raise NotImplementedError("parameter type '%s'" % info[0])

    def get_param(self, key, style=None):
        """Get the value of graphics parameter ``key``.  If the optional
        argument ``style`` is given, it must be a dictionary, mapping
        parameter names to values; in this case, values in ``style``
        override values set in the Canvas object.

        Args:
            key (string): the graphics parameter name to query.
            style (dict): graphics parameter values to override the
                canvas settings.

        """
        style = param.check_keys(style)
        return self._get_param(key, style)

    def _draw_text(self, text, x, y, font_size, col, bg,
                   horizontal_align, vertical_align, rotate, padding):
        padding = util._check_vec(padding, 4, True)
        p_top = util.convert_dim(padding[0], self.res, self.rect[3])
        p_right = util.convert_dim(padding[1], self.res, self.rect[2])
        p_bottom = util.convert_dim(padding[2], self.res, self.rect[3])
        p_left = util.convert_dim(padding[3], self.res, self.rect[2])

        self.ctx.save()
        self.ctx.set_font_matrix(
            cairo.Matrix(font_size, 0, 0, -font_size, 0, 0))

        ext = self.ctx.text_extents(text)
        if horizontal_align == "start":
            x_offs = 0
        elif horizontal_align == "end":
            x_offs = -ext[4]
        elif horizontal_align == "left":
            x_offs = -ext[0]
        elif horizontal_align == "right":
            x_offs = -ext[0] - ext[2]
        elif horizontal_align == "center":
            x_offs = -ext[0] - .5 * ext[2]
        else:
            x_offs = param.convert_dim(horizontal_align, self.res, ext[2])
        ascent, descent, line_height, _, _ = self.ctx.font_extents()
        if vertical_align == "baseline":
            y_offs = 0
        elif vertical_align == "top":
            y_offs = -ascent
        elif vertical_align == "bottom":
            y_offs = descent
        elif vertical_align == "center":
            y_offs = (descent - ascent) / 2
        else:
            y_offs = param.convert_dim(vertical_align, self.res, line_height)

        if bg is not None and bg[4] > 0:
            self.ctx.save()
            self.ctx.set_source_rgba(*bg)
            self.ctx.move_to(x, y)
            self.ctx.rotate(rotate)
            self.ctx.rel_move_to(ext[0] + x_offs - p_left,
                                 ext[1] + y_offs - p_bottom)
            self.ctx.rel_line_to(ext[2] + p_left + p_right, 0)
            self.ctx.rel_line_to(0, ext[3] + p_bottom + p_top)
            self.ctx.rel_line_to(- ext[2] - p_right - p_left, 0)
            self.ctx.close_path()
            self.ctx.fill()
            self.ctx.restore()

        self.ctx.set_source_rgba(*col)
        self.ctx.move_to(x, y)
        self.ctx.rotate(rotate)
        self.ctx.rel_move_to(x_offs, y_offs)
        self.ctx.show_text(text)
        self.ctx.restore()


class Canvas(Device):
    """Representation of a page which a plot can be drawn on.

    Canvas objects are normally created using the
    :py:func:`jvplot.Plot` function.  The methods of this class
    implement the various high-level plot types.

    Args:
        ctx (Cairo drawing context): The Cairo context used to draw
            the figure.

        rect (list of length 4): The extent of the drawing area, in
           device coordinates.  The four values `x, y, w, h = rect`
           represent the horizontal and vertical position of the
           drawing area on the page, and the width and hight of the
           drawing area, respectively.

        res (number): Resolution of the device, *i.e.* the number of
            device coordinate units per inch.

        style (dict, optional): Graphics parameters to override the
           default values.

        parent (Device, optional): used internally, for graphics
           parameters with value `"inherit"`.

    """

    def __init__(self, ctx, rect, *, res, style=None, parent=None):
        super().__init__(ctx, rect, res=res, style=style, parent=parent)

        # draw the background, if any
        r, g, b, a = self._get_param("bg_col", style)
        if a > 0 and ctx is not None:
            ctx.save()
            ctx.set_source_rgba(r, g, b, a)
            ctx.rectangle(*self.rect)
            ctx.fill()
            ctx.restore()

        # apply the padding
        padding_bottom = self._get_param('padding_bottom', style)
        padding_left = self._get_param('padding_left', style)
        padding_top = self._get_param('padding_top', style)
        padding_right = self._get_param('padding_right', style)
        self.rect[0] += padding_left
        self.rect[1] += padding_bottom
        self.rect[2] -= padding_left + padding_right
        self.rect[3] -= padding_bottom + padding_top

        self._on_close = []
        if parent:
            parent._on_close.append(self.close)

    def __str__(self):
        tmpl = "<Canvas %.0fx%.0f%+.0f%+.0f>"
        x, y, w, h = self.rect
        return tmpl % (w, h, x, y)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Call the ``close()`` method of the canvas."""
        self.close()

    def close(self):
        """Close the plot.

        This must be called once drawing is completed, either
        explicitly or by using the canvase as a context handler.

        After the plot is closed, nothing can be added any more.

        """
        while self._on_close:
            fn = self._on_close.pop()
            fn()
        self.ctx = None

    def plot(self, x, y=None, *, x_extra=None, y_extra=None, aspect=None,
             x_lim=None, y_lim=None, x_lab=None, y_lab=None, style=None):
        """Draw a line plot.

        Args:
            x ():
            y ():
            x_extra ():
            y_extra ():
            aspect ():
            x_lim ():
            y_lim ():
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        style = param.check_keys(style)
        x, y = util._check_coords(x, y)

        x_range = _spread(data_range(x, x_extra))
        y_range = _spread(data_range(y, y_extra))
        axes = self._add_axes(x_range, y_range, x_lim, y_lim, aspect, style,
                              x_lab=x_lab, y_lab=y_lab)
        axes.draw_lines(x, y)
        return axes

    def axes(self, x_range, y_range, *, aspect=None, x_lim=None, y_lim=None,
             x_lab=None, y_lab=None, style=None):
        style = param.check_keys(style)
        axes = self._add_axes(x_range, y_range, x_lim, y_lim, aspect, style,
                              x_lab=x_lab, y_lab=y_lab)
        return axes

    def _viewport(self, rect, x_range, y_range, style):
        """Get a new canvas representing a rectangular sub-region of the
        current canvas.

        Args:
            rect (list of length 4): the location of the viewport
                on the page.
            x_range ():
            y_range ():
            style (dict): graphics parameter values to override the
                canvas settings.

        """
        # allocate a new drawing context for the viewport
        surface = self.ctx.get_target()
        ctx = cairo.Context(surface)
        ctx.set_matrix(self.ctx.get_matrix())
        ctx.rectangle(*rect)
        ctx.clip()

        res = Axes(ctx, rect, x_range, y_range,
                   res=self.res, style=style, parent=self)

        return res

    def viewport(self, rect, x_range, y_range, *, style=None):
        """
        Args:
            rect ():
            x_range ():
            y_range ():
            style ():

        """
        style = param.check_keys(style)
        x_range = data_range(x_range)
        y_range = data_range(y_range)
        return self._viewport(rect, x_range, y_range, style)

    def subplot(self, cols, rows, idx=None, *, style=None):
        """Split the current canvas into a ``cols``-times-``rows`` grid and
        return the sub-canvas corresponding to column ``idx % cols``
        and row ``idx // cols`` (where both row and column counts
        start with 0).

        Args:
            cols (int): Number of columns.
            rows (int): Number of rows.
            idx (int): The position of the returned viewport in the grid.
            style (dict): graphics parameter values to override the
                canvas settings.

        """
        if rows <= 0 or cols <= 0:
            return ValueError('invalid %d by %d arrangement' % (cols, rows))
        style = param.check_keys(style)

        if idx is None:
            if (hasattr(self, '_last_subplot') and
                    self._last_subplot[0] == cols and
                    self._last_subplot[1] == rows):
                idx = (self._last_subplot[2] + 1) % (cols * rows)
            else:
                idx = 0
        if not 0 <= idx < cols * rows:
            tmpl = 'invalid index %d, not in range 0, ... %d'
            raise ValueError(tmpl % (idx, cols*rows-1))
        self._last_subplot = (cols, rows, idx)
        i = idx // cols
        j = idx % cols

        dw = self.rect[2] / cols
        dh = self.rect[3] / rows
        x0 = int(self.rect[0] + j*dw + .5)
        x1 = int(self.rect[0] + (j+1)*dw + .5)
        y0 = int(self.rect[1] + i*dh + .5)
        y1 = int(self.rect[1] + (i+1)*dh + .5)
        rect = [x0, y0, x1 - x0, y1 - y0]

        # allocate a new drawing context for the viewport
        surface = self.ctx.get_target()
        ctx = cairo.Context(surface)
        ctx.set_matrix(self.ctx.get_matrix())
        ctx.rectangle(*rect)
        ctx.clip()

        return Canvas(ctx, rect, res=self.res, style=style, parent=self)

    def scatter_plot(self, x, y=None, *, x_extra=None, y_extra=None,
                     aspect=None, x_lim=None, y_lim=None, style=None):
        """Draw a scatter plot.

        Args:
            x (array with ``shape=(n,)`` or ``shape=(n,2)``): The
                vertex coordinates of the points.  If `y` is
                given, `x` must be one-dimensional and the vertices
                are ``(x[0], y[0])``, ..., ``(x[n-1], y[n-1])``.
                Otherwise, `x` must be two-dimensional with two
                columns and the vertices are ``x[0,:]``, ...,
                ``x[n-1,:]``.
            y (array with ``shape=(n,)``, optional): See the
                description of `x`.
            x_extra ():
            y_extra ():
            aspect (number, optional): The aspect ratio of the axes
                area; 1 makes circles shown as circles, values >=1
                turn circles into ellipses wider than high, and values
                <=1 turn circles into ellipses higher than wide.
            x_lim (tuple): the horizontal coordinate range.
            y_lim (tuple): the vertical coordinate range.
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        style = param.check_keys(style)
        x, y = util._check_coords(x, y)

        x_range = _spread(data_range(x, x_extra))
        y_range = _spread(data_range(y, y_extra))
        axes = self._add_axes(x_range, y_range, x_lim, y_lim, aspect, style)
        axes.draw_points(x, y)
        return axes

    def pair_scatter_plot(self, z, *, names=None, upper_fn=None, diag_fn=None,
                          lower_fn=None, style=None):
        style = param.check_keys(style)

        z = np.array(z)
        if len(z.shape) != 2:
            raise ValueError("need two-dimensional data for a pair plot")
        _, p = z.shape
        if p > min(self.rect[2], self.rect[3]) / 36:
            raise ValueError("too many variables, plot area too small")
        mar_bottom = self._get_param('axis_margin_bottom', style)
        mar_left = self._get_param('axis_margin_left', style)
        mar_top = self._get_param('axis_margin_top', style)
        mar_right = self._get_param('axis_margin_right', style)
        mar_between = self._get_param('axis_margin_between', style)

        # self.rect[2] = mar_left + p*w + (p-1)*mar_between + mar_right
        w = (self.rect[2] - mar_left - (p-1)*mar_between - mar_right) / p
        # self.rect[3] = mar_bottom + p*h + (p-1)*mar_between + mar_top
        h = (self.rect[3] - mar_bottom - (p-1)*mar_between - mar_top) / p
        if w < 18 or h < 18:
            raise ValueError("margins too large, not enough space")

        ranges = [_spread(data_range(z[:, i])) for i in range(p)]
        if names is None:
            names = [None] * p
        elif len(names) != p:
            return ValueError(f"names must be alist of length {p}")

        rows = []
        for i in range(p):      # rows from bottom to top
            y = self.rect[1] + mar_bottom + i * (h + mar_between)

            row = []
            for j in range(p):  # colums from left to right
                if i > j:
                    fn = upper_fn
                elif i < j:
                    fn = lower_fn
                else:
                    fn = diag_fn

                x = self.rect[0] + mar_left + j * (w + mar_between)
                rect = [x, y, w, h]
                if fn == "blank":
                    ax = None
                else:
                    i_first = 0
                    if lower_fn == "blank":
                        i_first = j
                        if diag_fn == "blank":
                            i_first = j+1
                    j_first = 0
                    if upper_fn == "blank":
                        j_first = i
                        if diag_fn == "blank":
                            j_first = i+1
                    x_lab = names[j] if i == i_first else None
                    y_lab = names[i] if j == j_first else None
                    ax = self._add_axes2(rect,
                                         ranges[j], ranges[i], None, None,
                                         None, style,
                                         show_x_labels=(i == i_first),
                                         show_y_labels=(j == j_first),
                                         x_lab=x_lab,
                                         y_lab=y_lab)
                    if fn is None:
                        ax.draw_points(z[:, j], z[:, i])
                    else:
                        fn(ax, i, j)
                row.append(ax)
            rows.append(row)
        return np.array(rows)

    def histogram(self, x, *, bins=10, range=None, weights=None, density=False,
                  x_extra=None, y_extra=None, x_lim=None, y_lim=None,
                  style=None):
        """Draw a histogram.

        The arguments `x`, `bins`, `range`, `weights`, and `density`
        have the same meaning as for `numpy.histogram`.

        Args:
            x (array_like): Input data. The histogram is computed over
                the flattened array.
            bins (int or sequence of numbers, optional): If `bins` is
                an int, it defines the number of equal-width bins in
                the given range (10, by default). If `bins` is a
                sequence, it defines the bin edges, including the
                rightmost edge, allowing for non-uniform bin widths.
            range ((float, float), optional): The lower and upper range
                of the bins. If not provided, range is simply
                ``(x.min(), x.max())``.  Values outside the range are
                ignored.
            weights (array_like, optional): An array of weights, of
                the same shape as `x`.  Each value contributes its
                associated weight towards the bin count (instead of
                1).
            density (bool, optional): If ``False``, the result will
                contain the number of samples in each bin. If
                ``True``, the result is the value of the probability
                density function at the bin, normalized such that the
                integral over the range is 1.  Note that the sum of the
                histogram values will not be equal to 1 unless bins of
                unity width are chosen; it is not a probability mass
                function.
            x_extra ():
            y_extra ():
            x_lim ():
            y_lim ():
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        style = param.check_keys(style)
        hist, bin_edges = np.histogram(x, bins=bins, range=range,
                                       weights=weights, density=density)

        x_range = _spread(data_range(bin_edges, x_extra))
        y_range = _spread(data_range(hist, y_extra))
        axes = self._add_axes(x_range, y_range, x_lim, y_lim, None, style)
        axes.draw_histogram(hist, bin_edges, style=style)
        return axes

    def image(self, pixels, x_range=None, y_range=None, *, aspect=None,
              x_lab=None, y_lab=None, style=None):
        """Plot a raster image inside coordinate axes.

        The array ``pixels`` gives the pixel intensities, as RGB
        intensities in the range [0, 1].  The array must have the
        shape ``pix_height x pix_width x 3``, where the last
        coordinate indicates the colour channels in the order red,
        green, blue.

        args:
            pixels (array): the pixel intensities, in the form described
                above.
            x_range (tuple of length 2):
            y_range (tuple of length 2):
            style (dict, optional): Default plot graphics values for the
                canvas.

        """
        style = param.check_keys(style)

        pixels = np.array(pixels)
        if x_range is None:
            x_range = (0, pixels.shape[1])
        if y_range is None:
            y_range = (0, pixels.shape[0])
        axes = self._add_axes(x_range, y_range, None, None, aspect, style,
                              x_lab=x_lab, y_lab=y_lab)
        axes.draw_image(None, pixels, style=style)
        return axes

    def _add_axes(self, x_range, y_range, x_lim, y_lim, aspect, style, *,
                  x_lab=None, y_lab=None):
        """Draw a set of coordinate axes and return a new canvas representing
        the data area inside the axes.

        Args:
            x_range ():
            y_range ():
            x_lim (tuple): the horizontal coordinate range.
            y_lim (tuple): the vertical coordinate range.
            aspect (number): The aspect ratio of the axes area; 1
                makes circles shown as circles, values >=1 turn
                circles into ellipses wider than high, and values <=1
                turn circles into ellipses higher than wide.
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.
                The parameters in `style` are also used as the default
                parameters for the context representing the axes area.

        """
        margin_bottom = self._get_param('axis_margin_bottom', style)
        margin_left = self._get_param('axis_margin_left', style)
        margin_top = self._get_param('axis_margin_top', style)
        margin_right = self._get_param('axis_margin_right', style)
        border = self._get_param('axis_border', style)
        x = self.rect[0] + margin_left + border
        y = self.rect[1] + margin_bottom + border
        w = self.rect[2] - margin_left - margin_right - 2*border
        h = self.rect[3] - margin_bottom - margin_top - 2*border
        if w < 0 or h < 0:
            raise ValueError("not enough space, margins too large")
        return self._add_axes2([x, y, w, h], x_range, y_range, x_lim, y_lim,
                               aspect, style, x_lab=x_lab, y_lab=y_lab)

    def _add_axes2(self, rect, x_range, y_range, x_lim, y_lim,
                   aspect, style, *, x_lab=None, y_lab=None,
                   show_x_labels=True, show_y_labels=True):
        x, y, w, h = rect

        # axis graphics parameters
        tick_width = self._get_param('axis_tick_width', style)
        tick_length = self._get_param('axis_tick_length', style)
        x_label_dist = self._get_param('axis_x_label_dist', style)
        y_label_dist = self._get_param('axis_y_label_dist', style)
        tick_font_size = self._get_param('tick_font_size', style)
        label_font_size = self._get_param('label_font_size', style)
        label_font_col = self._get_param('label_font_col', style)
        border = self._get_param('axis_border', style)

        # layout parameters
        opt_spacing = self._get_param('axis_tick_opt_spacing', style)
        label_sep = self._get_param('axis_label_sep', style)

        # Temporarily switch the font, so we can determine label
        # dimensions:
        self.ctx.save()
        self.ctx.set_font_matrix(
            cairo.Matrix(tick_font_size, 0, 0, -tick_font_size, 0, 0))

        label_fn = lambda x: ["%g" % xi for xi in x]
        def width_fn(ticks):
            labels = label_fn(ticks)
            return [self.ctx.text_extents(lab)[4] for lab in labels]
        def height_fn(ticks):
            font_extents = self.ctx.font_extents()
            return [font_extents[2] for x in ticks]
        ax_x = coords.Linear(x_range, lim=x_lim)
        ax_y = coords.Linear(y_range, lim=y_lim)

        xa, xt, ya, yt = coords.ranges_and_ticks(
            w, h, ax_x, ax_y, width_fn, height_fn,
            label_sep, opt_spacing, aspect=aspect)

        x_labels = zip(xt, label_fn(xt))
        y_labels = zip(yt, label_fn(yt))
        ascent, descent, _, _, _ = self.ctx.font_extents()
        self.ctx.restore()

        s2 = {
            'padding_bottom': 0,
            'padding_left': 0,
            'padding_right': 0,
            'padding_top': 0,
        }
        s2.update(style)
        style = param.check_keys(s2)
        axes = self._viewport(rect, xa, ya, style)

        def decorate():
            self.ctx.save()
            if border > 0:
                self.ctx.rectangle(*rect)
                self.ctx.set_line_width(border)
                self.ctx.set_line_join(cairo.LINE_JOIN_MITER)
                self.ctx.stroke()

            self.ctx.set_line_cap(cairo.LINE_CAP_BUTT)
            self.ctx.set_line_width(tick_width)
            self.ctx.set_font_matrix(
                cairo.Matrix(tick_font_size, 0, 0, -tick_font_size, 0, 0))
            for x_pos, x_tlab in x_labels:
                x_pos = axes.data_to_dev_x(x_pos)
                ext = self.ctx.text_extents(x_tlab)
                self.ctx.move_to(x_pos, rect[1] - tick_length)
                self.ctx.line_to(x_pos, rect[1] + tick_length)
                if show_x_labels:
                    self.ctx.move_to(x_pos - .5*ext[4],
                                     rect[1] - tick_length - x_label_dist - ascent)
                    self.ctx.show_text(x_tlab)
            for y_pos, y_tlab in y_labels:
                y_pos = axes.data_to_dev_y(y_pos)
                ext = self.ctx.text_extents(y_tlab)
                self.ctx.move_to(rect[0] - tick_length, y_pos)
                self.ctx.line_to(rect[0] + tick_length, y_pos)
                if show_y_labels:
                    self.ctx.move_to(rect[0] - tick_length - y_label_dist - ext[4],
                                     y_pos - .5*(ascent - descent))
                    self.ctx.show_text(y_tlab)
            self.ctx.stroke()
            self.ctx.restore()

            if x_lab:
                self._draw_text(x_lab,
                                rect[0] + .5 * rect[2],
                                rect[1] - tick_length - 2 * x_label_dist - (ascent+descent),
                                label_font_size, label_font_col, None,
                                "center", "top", 0, ["1pt", "3pt"])
            if y_lab:
                self._draw_text(y_lab,
                                rect[0] - tick_length - 2 * y_label_dist - 3*(ascent+descent),
                                rect[1] + .5 * rect[3],
                                label_font_size, label_font_col, None,
                                "center", "top", np.pi/2, ["1pt", "3pt"])

        self._on_close.append(decorate)

        return axes


class Axes(Device):

    def __init__(self, ctx, rect, x_range, y_range, *, res, style=None, parent=None):
        super().__init__(ctx, rect, res=res, style=style, parent=parent)
        x_range = data_range(x_range)
        y_range = data_range(y_range)
        self.x_range = x_range
        self.y_range = y_range

        # The horizontal scale and offset are determined by the
        # following two equations:
        #     x_range[0] * x_scale + x_offset = x
        #     x_range[1] * x_scale + x_offset = x + w
        x_scale = self.rect[2] / (x_range[1] - x_range[0])
        x_offset = self.rect[0] - x_range[0] * x_scale
        # The vertical coordinates are similar:
        y_scale = self.rect[3] / (y_range[1] - y_range[0])
        y_offset = self.rect[1] - y_range[0] * y_scale
        self.offset = (x_offset, y_offset)
        self.scale = (x_scale, y_scale)

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

        self._draw_text(text, x, y, font_size, col, bg,
                        horizontal_align, vertical_align, rotate, padding)

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

        if x is not None:
            x = float(x)
            assert y is None and a is None and b is None
            x = self.offset[0] + x * self.scale[0]
            self.ctx.save()
            self.ctx.set_line_width(lw)
            self.ctx.set_source_rgba(*col)
            self.ctx.move_to(x, self._orig_y)
            self.ctx.line_to(x, self._orig_y + self._orig_height)
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
            assert x is None and y is None

        # self._orig_x = self.offset[0] + x0 * self.scale[0]
        x0 = (self._orig_x - self.offset[0]) / self.scale[0]
        y0 = a + b * x0
        # self._orig_x + self._orig_width = self.offset[0] + x1 * self.scale[0]
        x1 = (self._orig_x + self._orig_width - self.offset[0]) / self.scale[0]
        y1 = a + b * x1

        self.ctx.save()
        self.ctx.set_line_width(lw)
        self.ctx.set_source_rgba(*col)
        self.ctx.move_to(self._orig_x,
                         self.offset[1] + y0 * self.scale[1])
        self.ctx.line_to(self._orig_x + self._orig_width,
                         self.offset[1] + y1 * self.scale[1])
        self.ctx.stroke()
        self.ctx.restore()

    def draw_image(self, rect, pixels, *, style=None):
        """Draw a raster image onto the canvas.

        The array ``pixels`` gives the pixel intensities, as RGB
        intensities in the range [0, 1].  The array must have the
        shape ``pix_height x pix_width x 3``, where the last
        coordinate indicates the colour channels in the order red,
        green, blue.

        args:
            rect: A list of the form [x, y, w, h], which specifies the
                outermost edge of the image in data coordinates.
            pixels (array): the pixel intensities, in the form described
                above.
            style (dict, optional): Default plot graphics values for the
                canvas.

        """
        style = param.check_keys(style)

        if rect is None:
            rect = [
                self.x_range[0],
                self.y_range[0],
                self.x_range[1]-self.x_range[0],
                self.y_range[1]-self.y_range[0],
            ]
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

        if rect is not None:
            x0 = self.data_to_dev_x(rect[0])
            x1 = self.data_to_dev_x(rect[0] + rect[2])
            y0 = self.data_to_dev_y(rect[1])
            y1 = self.data_to_dev_y(rect[1] + rect[3])
        else:
            x0 = self.rect[0]
            x1 = self.rect[0] + self.rect[2]
            y0 = self.rect[1]
            y1 = self.rect[1] + self.rect[3]

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


def data_range(*args):
    lower = np.inf
    upper = -np.inf
    for arg in args:
        # ignore x_range and y_range default values
        if arg is None:
            continue

        # numbers are easy
        if isinstance(arg, (float, int)):
            if not np.isfinite(arg):
                continue
            if arg < lower:
                lower = arg
            if arg > upper:
                upper = arg
            continue

        # try whether numpy can deal with `arg`
        try:
            a = np.min(arg)
            b = np.max(arg)
        except ValueError:
            a = None
        if a is not None:
            if a < lower:
                lower = a
            if b > upper:
                upper = b
            continue

        # try whether `arg` is iterable
        try:
            for a2 in arg:
                a, b = data_range(a2)
                if a < lower:
                    lower = a
                if b > upper:
                    upper = b
        except TypeError:
            raise TypeError(f"invalid data range {arg!r}")
    if lower > upper:
        raise ValueError("no data range specified")
    return lower, upper

def _spread(rnge, f=0.05):
    a, b = rnge
    margin = f * (b - a)
    return a - margin, b + margin
