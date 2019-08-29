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

import numpy as np

import cairocffi as cairo

from . import axes
from . import device
from . import hist as histmod
from . import layout
from . import param
from . import scale
from . import util


class Canvas(device.Device):
    """Representation of a page which a plot can be drawn on.

    Canvas objects are normally created using the
    :py:func:`jvplot.Plot` function.  The methods of this class
    implement the various high-level plot types.

    """

    def __init__(self, ctx, rect, *, res, style=None, parent=None):
        """Create a new canvas object.

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
        """Finish the plot by drawing any outstanding overlays.

        This must be called once drawing is completed, either
        explicitly or by using the canvase as a context handler.

        After the plot is closed, nothing can be added any more.

        """
        while self._on_close:
            fn = self._on_close.pop()
            fn()

    def plot(self, x, y=None, *, rect=None, x_extra=None, y_extra=None,
             x_lim=None, y_lim=None, aspect=None, x_lab=None, y_lab=None,
             style=None):
        """Draw a line plot.

        Args:
            x (array with ``shape=(n,)`` or ``shape=(n,2)``): The
                vertex coordinates of the lines.  If `y` is
                given, `x` must be one-dimensional and the vertices
                are ``(x[0], y[0])``, ..., ``(x[n-1], y[n-1])``.
                Otherwise, `x` must be two-dimensional with two
                columns and the vertices are ``x[0, :]``, ...,
                ``x[n-1, :]``.
            y (array with ``shape=(n,)``, optional): See the
                description of `x`.
            rect ():
            x_extra ():
            y_extra ():
            x_lim (tuple): a pair of numbers, specifying the lower and upper
                coordinate range for the horizontal axis.
            y_lim (tuple): a pair of numbers, specifying the lower and upper
                coordinate range for the vertical axis.
            aspect (number): The aspect ratio of the axes area; 1
                makes circles shown as circles, values >=1 turn
                circles into ellipses wider than high, and values <=1
                turn circles into ellipses higher than wide.
            x_lab (str): the axis label for the vertical axis.
            x_lab (str): the axis label for the vertical axis.
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        style = param.check_keys(style)
        x, y = util._check_coords(x, y)

        x_range = self.data_range(x, x_extra)
        y_range = self.data_range(y, y_extra)
        rect = rect or self.get_margin_rect(style=style)
        ax = self._add_axes(rect, x_range, y_range, x_lim, y_lim,
                            aspect, style, x_lab=x_lab, y_lab=y_lab)
        ax.draw_lines(x, y)
        return ax

    def scatter_plot(self, x, y=None, *, x_extra=None, y_extra=None,
                     aspect=None, x_lim=None, y_lim=None, rect=None,
                     x_lab=None, y_lab=None, style=None):
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
            rect ():
            x_lab (str): the axis label for the vertical axis.
            x_lab (str): the axis label for the vertical axis.
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        style = param.check_keys(style)
        x, y = util._check_coords(x, y)

        x_range = self.data_range(x, x_extra)
        y_range = self.data_range(y, y_extra)
        rect = rect or self.get_margin_rect(style=style)
        ax = self._add_axes(rect, x_range, y_range, x_lim, y_lim, aspect, style,
                            x_lab=x_lab, y_lab=y_lab)
        ax.draw_points(x, y)
        return ax

    def band_plot(self, x, y_mid=None, y_lower=None, y_upper=None, *,
                  y_width=None, rect=None, x_extra=None, y_extra=None,
                  x_lim=None, y_lim=None, aspect=None, x_lab=None,
                  y_lab=None, style=None):
        """Draw a band plot.

        Args:
            x ():
            y_mid ():
            y_lower ():
            y_upper ():
            y_width ():
            rect ():
            x_extra ():
            y_extra ():
            x_lim (tuple): a pair of numbers, specifying the lower and upper
                coordinate range for the horizontal axis.
            y_lim (tuple): a pair of numbers, specifying the lower and upper
                coordinate range for the vertical axis.
            aspect (number): The aspect ratio of the axes; a value of 1
                displays mathematical circles visually as circles, values >1
                show circles as ellipses wider than high, and values <1 show
                circles as ellipses higher than wide.
            x_lab (str): the axis label for the vertical axis.
            x_lab (str): the axis label for the vertical axis.
            style ():

        """
        style = param.check_keys(style)
        x = np.array(x)
        if y_mid is not None:
            y_mid = np.array(y_mid)
        if y_width is not None:
            y_width = np.array(y_width)
        if y_lower is not None:
            y_lower = np.array(y_lower)
        elif y_mid is not None and y_width is not None:
            y_lower = y_mid - y_width
        else:
            raise ValueError("need to specify y_lower or y_mid and y_width")
        if y_upper is not None:
            y_upper = np.array(y_upper)
        elif y_mid is not None and y_width is not None:
            y_upper = y_mid + y_width
        else:
            raise ValueError("need to specify y_upper or y_mid and y_width")

        x_range = self.data_range(x, x_extra)
        y_range = self.data_range(y_mid, y_lower, y_upper, y_extra)
        rect = rect or self.get_margin_rect(style=style)
        ax = self._add_axes(rect, x_range, y_range, x_lim, y_lim, aspect, style,
                            x_lab=x_lab, y_lab=y_lab)
        ax._draw_band(x, y_lower, y_mid, y_upper, style)
        return ax

    def grid_plot(self, x_ranges, y_ranges=None, *, x_names=None, y_names=None,
                  upper_fn=None, diag_fn=None, lower_fn=None, style=None):
        """Create a grid of axes with aligned coordinate ranges.

        Args:
            x_ranges ():
            y_ranges ():
            x_names ():
            y_names ():
            upper_fn ():
            diag_fn ():
            lower_fn ():
            style ():

        Returns:
            A two-dimensional array, containing the axes created.

        """
        style = param.check_keys(style)
        if y_ranges is None:
            y_ranges = x_ranges
            y_names = y_names or x_names
        px = len(x_ranges)
        py = len(y_ranges)
        if px > self.rect[2] / 36 or py > self.rect[3] / 36:
            raise ValueError("too many variables, plot area too small")
        if x_names is None:
            x_names = [None] * px
        elif len(x_names) != px:
            return ValueError(f"x_names must be a list of length {px}")
        if y_names is None:
            y_names = [None] * py
        elif len(y_names) != py:
            return ValueError(f"y_names must be a list of length {py}")

        mar_bottom = self._get_param('margin_bottom', style)
        mar_left = self._get_param('margin_left', style)
        mar_top = self._get_param('margin_top', style)
        mar_right = self._get_param('margin_right', style)
        mar_between = self._get_param('margin_between', style)

        # self.rect[2] = mar_left + px*w + (px-1)*mar_between + mar_right
        w = (self.rect[2] - mar_left - (px-1)*mar_between - mar_right) / px
        # self.rect[3] = mar_bottom + py*h + (py-1)*mar_between + mar_top
        h = (self.rect[3] - mar_bottom - (py-1)*mar_between - mar_top) / py
        if w < 18 or h < 18:
            raise ValueError("margins too large, not enough space")

        base_ticks = self._get_param('axis_ticks', style)
        sub_ticks = {}
        for pos in 'bltr':
            if pos not in base_ticks.lower():
                sub_ticks[pos] = ('', '')
            elif pos in base_ticks:
                sub_ticks[pos] = (pos, pos)
            else:
                sub_ticks[pos] = (pos, pos.upper())
        base_labels = self._get_param('axis_labels', style)
        sub_labels = {}
        for pos in 'bltr':
            if pos in base_labels:
                sub_labels[pos] = ('', pos)
            else:
                sub_labels[pos] = ('', '')

        ax_rows = []
        for row in range(py):      # rows from bottom to top
            y = self.rect[1] + mar_bottom + row * (h + mar_between)

            ax_row = []
            for col in range(px):  # colums from left to right
                x = self.rect[0] + mar_left + col * (w + mar_between)
                rect = [x, y, w, h]

                if row > col:
                    fn = upper_fn
                elif row < col:
                    fn = lower_fn
                else:
                    fn = diag_fn

                if fn == "blank":
                    ax_row.append(None)
                    continue

                rr = []
                cc = []
                if diag_fn != "blank":
                    rr.append(col)
                    cc.append(row)
                if upper_fn != "blank":
                    if col+1 < px:
                        rr.extend(range(col+1, px))
                    if row > 0:
                        cc.extend(range(row))
                if lower_fn != "blank":
                    if col > 0:
                        rr.extend(range(col))
                    if row+1 < py:
                        cc.extend(range(row+1, py))


                axis_ticks = (sub_ticks['b'][row == min(rr)] +
                              sub_ticks['l'][col == min(cc)] +
                              sub_ticks['t'][row == max(rr)] +
                              sub_ticks['r'][col == max(cc)])
                axis_labels = (sub_labels['b'][row == min(rr)] +
                               sub_labels['l'][col == min(cc)] +
                               sub_labels['t'][row == max(rr)] +
                               sub_labels['r'][col == max(cc)])
                s_xy = param.merge(style,
                                   axis_ticks=axis_ticks,
                                   axis_labels=axis_labels)
                if fn is None:
                    ax = self._add_axes(rect, x_ranges[col], y_ranges[row],
                                        None, None, None, s_xy,
                                        x_lab=x_names[col],
                                        y_lab=y_names[row])
                else:
                    ax = fn(self, row, col, rect, x_ranges[col], y_ranges[row],
                            s_xy)
                ax_row.append(ax)
            ax_rows.append(ax_row)
        return np.array(ax_rows)

    def pair_scatter_plot(self, z, *, names=None, upper_fn=None, diag_fn=None,
                          lower_fn=None, style=None):
        """Create a new pair scatter plot.

        Args:
            z ():
            names ():
            upper_fn ():
            diag_fn ():
            lower_fn ():
            style ():

        """
        style = param.check_keys(style)

        z = np.array(z)
        if len(z.shape) != 2:
            raise ValueError("need two-dimensional data for a pair plot")
        _, p = z.shape
        ranges = [self.data_range(z[:, i]) for i in range(p)]

        grid = self.grid_plot(ranges, x_names=names, upper_fn=upper_fn,
                              diag_fn=diag_fn, lower_fn=lower_fn, style=style)

        for row in range(p):      # rows from bottom to top
            for col in range(p):  # colums from left to right
                if row > col:
                    fn = upper_fn
                elif row < col:
                    fn = lower_fn
                else:
                    fn = diag_fn

                if fn is None:
                    ax = grid[row, col]
                    ax.draw_points(z[:, col], z[:, row])
        return grid

    def histogram(self, x, *, bins=None, range=None, weights=None, density=False,
                  x_extra=None, y_extra=None, x_lim=None, y_lim=None,
                  x_lab=None, y_lab=None, rect=None, style=None):
        """Draw a histogram.

        The arguments `x`, `bins`, `range`, `weights`, and `density`
        have the same meaning as for `numpy.histogram`.

        Args:
            x (array_like): Input data. The histogram is computed over
                the flattened array.
            bins (int or sequence of numbers, optional): If `bins` is
                an int, it defines the number of equal-width bins in
                the given range. If `bins` is a sequence, it defines
                the bin edges, including the rightmost edge, allowing
                for non-uniform bin widths.  If `bins` is not set,
                a heuristic is used.
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
            x_lim (tuple): a pair of numbers, specifying the lower and upper
                coordinate range for the horizontal axis.
            y_lim (tuple): a pair of numbers, specifying the lower and upper
                coordinate range for the vertical axis.
            x_lab (str): the axis label for the vertical axis.
            x_lab (str): the axis label for the vertical axis.
            rect ():
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        style = param.check_keys(style)
        x = np.array(x)
        if bins is None:
            bins = histmod.guess_bins(x)
        hist, bin_edges = np.histogram(x, bins=bins, range=range,
                                       weights=weights, density=density)

        x_range = self.data_range(bin_edges, x_extra)
        y_range = self.data_range(hist, y_extra)
        rect = rect or self.get_margin_rect(style=style)
        ax = self._add_axes(rect, x_range, y_range, x_lim, y_lim, None, style,
                            x_lab=x_lab, y_lab=y_lab)
        ax.draw_histogram(hist, bin_edges, style=style)
        return ax

    def image(self, pixels, x_range=None, y_range=None, *, aspect=None,
              x_lab=None, y_lab=None, rect=None, style=None):
        """Plot a raster image inside coordinate axes.

        The array ``pixels`` gives the pixel intensities, as RGB
        intensities in the range [0, 1].  The array must have the
        shape ``pix_height x pix_width x 3``, where the last
        coordinate indicates the colour channels in the order red,
        green, blue.

        Args:
            pixels (array): the pixel intensities, in the form described
                above.
            x_range (tuple of length 2):
            y_range (tuple of length 2):
            aspect (number): The aspect ratio of the axes; a value of 1
                displays mathematical circles visually as circles, values >1
                show circles as ellipses wider than high, and values <1 show
                circles as ellipses higher than wide.
            x_lab (str): the axis label for the vertical axis.
            x_lab (str): the axis label for the vertical axis.
            rect ():
            style (dict, optional): Default plot graphics values for the
                canvas.

        """
        style = param.check_keys(style)
        pixels = np.array(pixels)

        if x_range is None:
            x_range = (0, pixels.shape[1])
        if y_range is None:
            y_range = (0, pixels.shape[0])
        rect = rect or self.get_margin_rect(style=style)
        ax = self._add_axes(rect, x_range, y_range, None, None, aspect, style,
                            x_lab=x_lab, y_lab=y_lab)
        ax.draw_image(pixels, style=style)
        return ax

    def axes(self, *, x_range=None, y_range=None, x_lim=None, y_lim=None,
             aspect=None, rect=None, x_lab=None, y_lab=None, style=None):
        """Draw a set of coordinate axes and return a new Axes object
        representing the data area inside the axes.

        Args:
            x_range (tuple): The horizontal coordinate range to cover.
                The actual axis range may be larger than this.
            y_range (tuple): The vertical coordinate range to cover.
                The actual axis range chosen may be larger than this.
            x_lim (tuple): The exact coordinate range for the
                horizontal axis.
            y_lim (tuple): The exact coordinate range for the vertical
                axis.
            aspect (number): The aspect ratio of the axes; a value of 1
                displays mathematical circles visually as circles, values >1
                show circles as ellipses wider than high, and values <1 show
                circles as ellipses higher than wide.
            rect():
            x_lab (str): the axis label for the vertical axis.
            x_lab (str): the axis label for the vertical axis.
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.
                The parameters in `style` are also used as the default
                parameters for the context representing the axes area.

        """
        style = param.check_keys(style)
        rect = rect or self.get_margin_rect(style=style)
        ax = self._add_axes(rect, x_range, y_range, x_lim, y_lim, aspect,
                            style, x_lab=x_lab, y_lab=y_lab)
        return ax

    def color_bar(self, color_scale, *, rect=None, discrete=False, steps=100,
                  y_lab=None, style=None):
        """Draw a colour bar onto the canvas.

        Args:
            color_scale ():
            rect ():
            discrete ():
            steps ():
            x_lab (str): the axis label for the vertical axis.
            style ():
            x_lab (str): the axis label for the vertical axis.

        """
        style = param.check_keys(style)

        if rect is None:
            color_bar_width = self._get_param('color_bar_width', style)
            margin_left = self._get_param('margin_left', style)
            rect = self.get_margin_rect(style=style)
            rect[0] = rect[0] + rect[2] - color_bar_width
            rect[2] = color_bar_width
            self.rect[2] -= margin_left + color_bar_width
        lw = self._get_param('color_bar_border_lw', style)
        style = param.update(style, parent_style=self.style,
                             axis_ticks='L',
                             axis_border_lw=lw,
                             padding=0)
        ax = self._add_axes(rect, None, color_scale.data_range(),
                            (0, 1), None, None, style, y_lab=y_lab)

        y_range = ax.y_range
        if discrete:
            y_range = (np.round(y_range[0])-.5, np.round(y_range[1])+.5)
            if steps > y_range[1] - y_range[0]:
                steps = int(y_range[1] - y_range[0])
        steps = np.linspace(y_range[0], y_range[1], steps).reshape((-1, 1))
        img = color_scale(steps)
        ax.draw_image(img, [0, 1], y_range)

        return ax

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

    def _add_axes(self, rect, x_range, y_range, x_lim, y_lim,
                  aspect, style, *, x_lab=None, y_lab=None):
        if not (x_range or x_lim):
            raise ValueError("need to specify either x_range or x_lim")
        if not (y_range or y_lim):
            raise ValueError("need to specify either y_range or y_lim")

        padding_bottom = self._get_param('padding_bottom', style,
                                         use_default=True)
        padding_left = self._get_param('padding_left', style,
                                       use_default=True)
        padding_top = self._get_param('padding_top', style,
                                      use_default=True)
        padding_right = self._get_param('padding_right', style,
                                        use_default=True)
        tick_font_size = self._get_param('tick_font_size', style)
        opt_spacing_x = self._get_param('axis_tick_spacing_x', style)
        opt_spacing_y = self._get_param('axis_tick_spacing_y', style)

        get_width = lambda lab: self.text_width(lab, tick_font_size)
        get_height = lambda lab: self.font_height(tick_font_size)

        _, _, w, h = rect
        if w <= padding_left + padding_right or h <= padding_top + padding_bottom:
            raise ValueError("padding too large, not enough space")

        s = scale.Linear()
        lx = layout.Layout(w, (padding_left, padding_right), x_range,
                           lim=x_lim,
                           dev_opt_dist=opt_spacing_x,
                           dev_width_fn=get_width,
                           can_shift=True,
                           scale=s)
        ly = layout.Layout(h, (padding_bottom, padding_top), y_range,
                           lim=y_lim,
                           dev_opt_dist=opt_spacing_y,
                           dev_width_fn=get_height,
                           scale=s)
        l = layout.Layout2D(lx, ly)
        l.fix(aspect=aspect)

        xa = lx.data_margins()
        ya = ly.data_margins()
        ax = axes.Axes(self, rect, xa, ya, style=style)

        style = style.copy()
        def decorate():
            ticks = self._get_param('axis_ticks', style)
            labels = self._get_param('axis_labels', style)

            ax.decorate()
            for pos in 'bt':
                if pos not in ticks.lower():
                    continue
                x_labels = lx.labels if pos.upper() in ticks else None
                ax._draw_ticks(lx.ticks, x_labels, pos, style)
            for pos in 'lr':
                if pos not in ticks.lower():
                    continue
                y_labels = ly.labels if pos.upper() in ticks else None
                ax._draw_ticks(ly.ticks, y_labels, pos, style)

            for pos in 'bt':
                if not x_lab or pos not in labels:
                    continue
                ax._draw_axis_label(x_lab, pos, style)
            for pos in 'lr':
                if not y_lab or pos not in labels:
                    continue
                ax._draw_axis_label(y_lab, pos, style)

        self._on_close.append(decorate)

        return ax
