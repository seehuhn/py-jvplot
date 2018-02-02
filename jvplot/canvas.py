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
from . import color
from . import errors
from . import param
from . import util


def _prepare_context(ctx):
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)


def _fixup_lim(lim, data=None):
    if lim is None and data is not None:
        lim = (None, None)
    try:
        a, b = tuple(lim)
    except:
        tmpl = 'axis limit must be a pair, not "%s"'
        raise TypeError(tmpl % repr(lim))

    if a is None and data is not None:
        a = np.nanmin(data)
    if b is None and data is not None:
        b = np.nanmax(data)
    try:
        a = float(a)
        b = float(b)
    except:
        tmpl = 'axis limit must be pair of numbers, not "%s"'
        raise TypeError(tmpl % repr(lim))
    if b < a:
        tmpl = 'lower bound %s must not be larger than upper bound %s'
        raise ValueError(tmpl % lim)

    if a != b:
        return (a, b)
    if a == 0:
        return (-1, 1)
    return (min(a, 0), max(a, 0))


class Canvas:
    """The Canvas class.  Canvas objects are normally created using
    the :py:func:`jvplot.Plot` function.

    Args:
        ctx (Cairo drawing context): The Cairo context used to draw
            the figure.

        x (number): the horizontal position of the left canvas edge on
            the drawing context, in device coordinates.

        x (number): the vertical position of the bottom canvas edge on
            the drawing context, in device coordinates.

        w (number): the width of the canvas in device coordinate
            units.

        h (number): the height of the canvas in device coordinate
            units.

        res (number):Resolution of the canvas, *i.e.* the number of
            device coordinate units per inch.

        parent (Canvas or None): The parent canvas, or ``None`` for
            the root canvas.

        style (dict, optional): Default plot graphics values for the
            canvas.

    """

    def __init__(self, ctx, x, y, w, h, *, res, parent, style=None):
        """Allocate a new canvas."""
        style = self._check_style(style)

        self.ctx = ctx

        self.x = x
        """Horizontal position of this canvas on the parent canvas, in device
        coordinate units (read only).

        """

        self.y = y
        """Vertical position of this canvas on the parent canvas, in device
        coordinate units (read only).

        """

        self.width = w
        "Width of the canvas in device coordinate units (read only)."

        self.height = h
        "Height of the canvas in device coordinate units (read only)."

        self._orig_x = self.x
        self._orig_y = self.y
        self._orig_width = self.width
        self._orig_height = self.height

        self.res = res
        """Resolution of the canvas, *i.e.* the number of device coordinate
        units per inch (read only)."""

        self.parent = parent
        self.style = style if style is not None else {}

        self.offset = None
        self.scale = None
        self.axes = None

    def __str__(self):
        tmpl = "<Canvas %.0fx%.0f%+.0f%+.0f>"
        return tmpl % (self.width, self.height, self.x, self.y)

    @staticmethod
    def _check_style(style):
        if style is None:
            return {}
        style = dict(style)
        invalid = style.keys() - param.valid_keys
        for name in invalid:
            msg = "invalid style parameter '%s'" % name
            raise errors.InvalidParameterName(msg)
        return style

    def get_param(self, name, style=None):
        """Get the value of graphics parameter ``name``.  If the optional
        argument ``style`` is given, it must be a dictionary, mapping
        parameter names to values; in this case, values in ``style``
        override values set in the Canvas object.

        Args:
            name (string): the graphics parameter name to query.
            style (dict): graphics parameter values to override the
                canvas settings.

        """
        info = param.default.get(name)
        if info is None:
            msg = "unknown parameter '%s'" % name
            raise errors.InvalidParameterName(msg)

        elem = self
        if style is not None:
            style = self._check_style(style)
            style0 = elem.style.copy()
            style0.update(style)
        else:
            style0 = elem.style

        names = [name]
        style = style0
        while True:
            value = style.get(name)
            print(name, value, style)
            if value is None:
                value = info[1]
            if isinstance(value, str) and value.startswith('$'):
                name = value[1:]
                if name in names:
                    msg = ' -> '.join(names + [name])
                    raise errors.WrongUsage("infinite parameter loop: " + msg)
                names.append(name)
                info = param.default.get(name)
                elem = self
                style = style0
            elif value == "inherit":
                elem = elem.parent
                style = elem.style
            else:
                break
        if info[0] == 'width':
            return util.convert_dim(value, self.res, self.width)
        elif info[0] == 'height':
            return util.convert_dim(value, self.res, self.height)
        elif info[0] == 'dim':
            return util.convert_dim(value, self.res)
        elif info[0] == 'col':
            return color.get(value)
        elif info[0] == 'bool':
            return bool(value)
        else:
            raise NotImplementedError("parameter type '%s'" % info[0])

    def add_padding(self, padding):
        """Add extra padding around the inside edge of the canvas.  This
        function reduces the size of the canvas.

        Args:
            padding (string or tuple of length 4): the amount of
                margin to add at the top, right, bottom and left edge.

        """
        if self.axes is not None:
            msg = "cannot add padding once axes are present"
            raise errors.WrongUsage(msg)

        padding = util._check_vec(padding, 4, True)
        p_top = util.convert_dim(padding[0], self.res, self.height)
        p_right = util.convert_dim(padding[1], self.res, self.width)
        p_bottom = util.convert_dim(padding[2], self.res, self.height)
        p_left = util.convert_dim(padding[3], self.res, self.width)
        self.x += p_left
        self.width -= p_left + p_right
        self.y += p_bottom
        self.height -= p_bottom + p_top

    def add_title(self, text, *, style=None):
        """Add a title showing the string ``text`` along the top edge of the
        canvas.  This function reduces the height of the canvas.

        Args:
            text (string): The title text to add.
            style (dict): graphics parameter values to override the
                canvas settings.

        This function uses the following graphics parameters:

            - title_font_size: the font size to use to typeset the
              title.

            - title_top_margin: the size of the margin to add between
              the bottom of the title text and the top of the
              remaining canvas.

        """
        if self.axes is not None:
            raise errors.WrongUsage("cannot add title once axes are present")

        style = self._check_style(style)
        font_size = self.get_param('title_font_size', style)
        margin = self.get_param('title_top_margin', style)

        self.ctx.save()
        self.ctx.set_font_matrix(
            cairo.Matrix(font_size, 0, 0, -font_size, 0, 0))
        ascent, descent, _, _, _ = self.ctx.font_extents()
        self.height -= ascent + descent + margin
        if self.height < 0:
            msg = "plot is not high enough to add a title"
            raise errors.WrongUsage(msg)

        ext = self.ctx.text_extents(text)
        x_offs = max((self.width - ext[2]) / 2, 0)
        x_offs -= ext[0]
        self.ctx.move_to(self.x + x_offs, self.y + self.height + descent)
        self.ctx.show_text(text)
        self.ctx.restore()

    def set_limits(self, x_lim, y_lim):
        """Set the transformation from data to canvas coordinates.  This
        method must be called before any data can be plotted on the
        canvas.

        Args:
            x_lim (tuple of length 2): A pair of numbers, giving the
                minimal/maximal x-coordinate of the data.
            y_lim (tuple of length 2): A pair of numbers, giving the
                minimal/maximal y-coordinate of the data.

        """
        x_lim = util._check_range(x_lim)
        y_lim = util._check_range(y_lim)

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
        """Args:
            width (dim): The width of the viewport.
            height (dim): The height of the viewport.
            margin (string or tuple of length 4): margins, determining
                the position of the viewport on the canvas.
            border (dim): Line width of the border box.
            padding (string or tuple of length 4): Amount of padding
                inside the edge of the new viewport.
            style (dict): graphics parameter values to override the
                canvas settings.

        Returns:
            A pair `(axes, rect)` consisting of the new canvas object
            `axes` and the outside edge of the axes box border line in
            `rect`, reported as a 4-tuple `(x, y, width, hight)` in
            device coordinates.

        """
        width = util.convert_dim(width, self.res, self.width)
        height = util.convert_dim(height, self.res, self.height)

        margin = util._check_vec(margin, 4, True)
        m_top = util.convert_dim(margin[0], self.res, self.height)
        m_right = util.convert_dim(margin[1], self.res, self.width)
        m_bottom = util.convert_dim(margin[2], self.res, self.height)
        m_left = util.convert_dim(margin[3], self.res, self.width)

        if isinstance(border, str):
            border = border.split()
            border_width = border[0]
        else:
            border_width = border
        border_width = util.convert_dim(border_width, self.res)
        if border_width < 0:
            raise ValueError('negative border width in "%s"' % border)

        padding = util._check_vec(padding, 4, True)
        p_top = util.convert_dim(padding[0], self.res, self.height)
        p_right = util.convert_dim(padding[1], self.res, self.width)
        p_bottom = util.convert_dim(padding[2], self.res, self.height)
        p_left = util.convert_dim(padding[3], self.res, self.width)

        total_w = sum(x for x in [m_left, border_width, p_left, width,
                                  p_right, border_width, m_right]
                      if x is not None)
        if total_w > 1.001 * self.width:
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
        if total_h > 1.001 * self.height:
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

        res = Canvas(ctx, x, y, w, h, res=self.res, parent=self, style=style)
        res.add_padding([p_top / self.res, p_right / self.res,
                         p_bottom / self.res, p_left / self.res])
        return res, border_rect

    def viewport(self, *, width=None, height=None, margin=None, border=0,
                 padding=0, style=None):
        """Get a new canvas representing a rectangular sub-region of the
        current canvas.

        Args:
            width (dim): The width of the viewport.
            height (dim): The height of the viewport.
            margin (string or tuple of length 4): margins, determining
                the position of the viewport on the canvas.
            border (dim): Line width of the border box.
            padding (string or tuple of length 4): Amount of padding
                inside the edge of the new viewport.
            style (dict): graphics parameter values to override the
                canvas settings.

        """
        style = self._check_style(style)
        res, _ = self._viewport(width, height, margin, border, padding, style)
        return res

    def subplot(self, cols, rows, idx=None, *, padding=0, style=None):
        """Split the current canvas into a ``cols``-times-``rows`` grid and
        return the sub-canvas corresponding to column ``idx % cols``
        and row ``idx // cols`` (where both row and column counts
        start with 0).

        Args:
            cols (int): Number of columns.
            rows (int): Number of rows.
            idx (int): The position of the returned viewport in the grid.
            padding (string or tuple of length 4): Amount of padding
                inside the edge of the new viewport.
            style (dict): graphics parameter values to override the
                canvas settings.

        """
        if rows <= 0 or cols <= 0:
            return ValueError('invalid %d by %d arrangement' % (cols, rows))
        style = self._check_style(style)

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
        dw = self.width / cols / self.res
        dh = self.height / rows / self.res
        return self.viewport(width=dw, height=dh,
                             margin=[None, None, i*dh, j*dw],
                             padding=padding)

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
        style = self._check_style(style)
        font_size = self.get_param('text_font_size', style)
        col = self.get_param('text_col', style)
        bg = self.get_param('text_bg', style)

        x, y = util._check_coord_pair(x, y)
        x = self.offset[0] + self.scale[0] * x
        y = self.offset[1] + self.scale[1] * y

        if rotate_deg is not None:
            rotate = float(rotate_deg) / 180 * np.pi

        padding = util._check_vec(padding, 4, True)
        p_top = util.convert_dim(padding[0], self.res, self.height)
        p_right = util.convert_dim(padding[1], self.res, self.width)
        p_bottom = util.convert_dim(padding[2], self.res, self.height)
        p_left = util.convert_dim(padding[3], self.res, self.width)

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

        if bg is not None:
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

    def _layout_labels(self, x_lim, y_lim, aspect, font_ctx):
        """
        Args:
            x_lim ():
            y_lim ():
            aspect ():
            font_ctx ():

        """
        opt_spacing = self.get_param('axis_tick_opt_spacing')
        x_label_sep = self.get_param('axis_x_label_sep')
        if aspect is None:
            # horizontal axis
            best_p = np.inf
            for lim, steps in axis._try_single(x_lim):
                labels = ["%g" % pos for pos in steps]
                p = axis._penalties(self.width, x_lim, lim, steps, labels,
                                    True, font_ctx, x_label_sep,
                                    min(self.width/2, opt_spacing))
                ps = np.array([1.0, 1.0, 1.0, 1.0]).dot(p)
                if ps < best_p:
                    best_p = ps
                    best_xlim = lim
                    best_xsteps = steps
                    best_xlabels = labels

            # vertical axis
            best_p = np.inf
            for lim, steps in axis._try_single(y_lim):
                labels = ["%g" % pos for pos in steps]
                p = axis._penalties(self.height, y_lim, lim, steps, labels,
                                    False, font_ctx, 0.0,
                                    min(self.height/2, opt_spacing))
                ps = np.array([1.0, 1.0, 1.0, 1.0]).dot(p)
                if ps < best_p:
                    best_p = ps
                    best_ylim = lim
                    best_ysteps = steps
                    best_ylabels = labels
        else: # aspect ratio is set
            best_p = np.inf
            q = aspect * self.width / self.height
            for data in axis._try_pairs(x_lim, y_lim, q):
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

    def draw_axes(self, x_lim, y_lim, *, x_label=None, y_label=None,
                  aspect=None, width=None, height=None, margin=None,
                  border=None, padding=None, style=None):
        """Draw a set of coordinate axes and return a new canvas representing
        the data area inside the axes.

        Args:
            x_lim (tuple): the horizontal coordinate range.
            y_lim (tuple): the vertical coordinate range.
            x_label (string, optional): the x-axis label.
            y_label (string, optional): the y-axis label.
            aspect (number, optional): The aspect ratio of the axes
                area; 1 makes circles shown as circles, values >=1
                turn circles into ellipses wider than high, and values
                <=1 turn circles into ellipses higher than wide.
            width (dimension, optional): the width of the axes area.
            height (dimension, optional): the height of the axes area.
            margin (dimension, optional): the width of the outer margin
                around the axes area.
            border (border): space to leave between the axis box and
                the inside edge of the current canvas.
            padding (border): space to leave around the inside edge of
                the new axis box.
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.
                The parameters in `style` are also used as the default
                parameters for the context representing the axes area.

        """
        style = self._check_style(style)
        if margin is None:
            margin = [None, None, None, None]
        else:
            margin = util._check_vec(margin, 4, True)
        if margin[0] is None:
            margin[0] = self.get_param('axis_margin_top', style) / self.res
        if margin[1] is None:
            margin[1] = self.get_param('axis_margin_right', style) / self.res
        if margin[2] is None:
            margin[2] = self.get_param('axis_margin_bottom', style) / self.res
        if margin[3] is None:
            margin[3] = self.get_param('axis_margin_left', style) / self.res
        if border is None:
            border = self.get_param('axis_lw', style) / self.res
        if padding is None:
            padding = "2mm"

        axes, rect = self._viewport(width, height, margin, border, padding,
                                    style)
        tick_width = axes.get_param('axis_tick_width')
        tick_length = axes.get_param('axis_tick_length')
        x_label_dist = axes.get_param('axis_x_label_dist')
        y_label_dist = axes.get_param('axis_y_label_dist')
        tick_font_size = axes.get_param('axis_font_size')

        self.ctx.save()

        self.ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        self.ctx.set_line_width(tick_width)
        self.ctx.set_font_matrix(
            cairo.Matrix(tick_font_size, 0, 0, -tick_font_size, 0, 0))
        ascent, descent, _, _, _ = self.ctx.font_extents()
        x_tick_bottom = rect[1] - tick_length - x_label_dist - ascent + descent

        x_lim = _fixup_lim(x_lim)
        y_lim = _fixup_lim(y_lim)
        x_lim, x_labels, y_lim, y_labels = axes._layout_labels(
            x_lim, y_lim, aspect, self.ctx)
        axes.set_limits(x_lim, y_lim)

        for x_pos, x_lab in x_labels:
            x_pos = axes.offset[0] + x_pos * axes.scale[0]
            ext = self.ctx.text_extents(x_lab)
            self.ctx.move_to(x_pos, rect[1] - tick_length)
            self.ctx.line_to(x_pos, rect[1] + tick_length)
            self.ctx.move_to(x_pos - .5*ext[4],
                             rect[1] - tick_length - x_label_dist - ascent)
            self.ctx.show_text(x_lab)
        for y_pos, y_lab in y_labels:
            y_pos = axes.offset[1] + y_pos * axes.scale[1]
            ext = self.ctx.text_extents(y_lab)
            self.ctx.move_to(rect[0] - tick_length, y_pos)
            self.ctx.line_to(rect[0] + tick_length, y_pos)
            self.ctx.move_to(rect[0] - tick_length - y_label_dist - ext[4],
                             y_pos - .5*(ascent - descent))
            self.ctx.show_text(y_lab)
        self.ctx.stroke()

        if x_label:
            label_font_size = axes.get_param('axis_label_font_size')
            self.ctx.set_font_matrix(
                cairo.Matrix(tick_font_size, 0, 0, -tick_font_size, 0, 0))
            ascent, descent, _, _, _ = self.ctx.font_extents()
            ext = self.ctx.text_extents(x_label)
            self.ctx.move_to(rect[0] + .5*rect[2] - .5*ext[4],
                             x_tick_bottom - ascent)
            self.ctx.show_text(x_label)
            self.ctx.stroke()

        self.ctx.restore()

        axes.x_lim = x_lim
        axes.x_labels = x_labels
        axes.y_lim = y_lim
        axes.y_labels = y_labels
        self.axes = axes

        return axes

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
        style = self._check_style(style)
        lw = self.get_param('plot_lw', style)
        col = self.get_param('plot_col', style)

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

    def plot(self, x, y=None, *, aspect=None, x_lim=None, y_lim=None,
             width=None, height=None, margin=None, border=None, padding=None,
             style=None):
        """Draw a line plot.

        Args:
            x ():
            y ():
            aspect ():
            x_lim ():
            y_lim ():
            width ():
            height ():
            margin ():
            border ():
            padding ():
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        if self.axes is None:
            x, y = util._check_coords(x, y)
            x_lim = _fixup_lim(x_lim, x)
            y_lim = _fixup_lim(y_lim, y)
            self.draw_axes(
                x_lim, y_lim, aspect=aspect, width=width,
                height=height, margin=margin, border=border, padding=padding,
                style=style)
        self.axes.draw_lines(x, y, style=style)
        return self.axes

    def draw_points(self, x, y=None, *, style=None):
        """
        Args:
            x ():
            y ():
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        style = self._check_style(style)
        lw = self.get_param('plot_point_size', style)
        col = self.get_param('plot_point_col', style)
        separate = self.get_param('plot_point_separate', style)

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

    def scatter_plot(self, x, y=None, *, x_lim=None, y_lim=None,
                     x_label=None, y_label=None, aspect=None, width=None,
                     height=None, margin=None, border=None, padding=None,
                     style=None):
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
            x_lim (tuple): the horizontal coordinate range.
            y_lim (tuple): the vertical coordinate range.
            x_label (string, optional): the x-axis label.
            y_label (string, optional): the y-axis label.
            aspect (number, optional): The aspect ratio of the axes
                area; 1 makes circles shown as circles, values >=1
                turn circles into ellipses wider than high, and values
                <=1 turn circles into ellipses higher than wide.
            width (dimension, optional): the width of the axes area.
            height (dimension, optional): the height of the axes area.
            margin (dimension, optional): the width of the outer margin
                around the axes area.
            border (border): space to leave between the axis box and
                the inside edge of the current canvas.
            padding (border): space to leave around the inside edge of
                the new axis box.
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        if self.axes is None:
            x, y = util._check_coords(x, y)
            x_lim = _fixup_lim(x_lim, x)
            y_lim = _fixup_lim(y_lim, y)
            self.draw_axes(x_lim, y_lim, x_label=x_label,
                           y_label=y_label, aspect=aspect, width=width,
                           height=height, margin=margin, border=border,
                           padding=padding, style=style)
        self.axes.draw_points(x, y)
        return self.axes

    def draw_histogram(self, hist, bin_edges, *, style=None):
        """
        Args:
            hist (array): the data to plot.
            bin_edges (array): a vector of bin edges.
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        style = self._check_style(style)
        lc = self.get_param('hist_col', style)
        lw = self.get_param('hist_lw', style)
        fc = self.get_param('hist_fill_col', style)

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

    def histogram(self, x, *, bins=10, range=None, weights=None,
                  density=False, x_lim=None, y_lim=None, width=None,
                  height=None, margin=None, border=None, padding=None,
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
            x_lim ():
            y_lim ():
            width ():
            height ():
            margin ():
            border ():
            padding ():
            style (dict): graphics parameter values to override the
                canvas settings, setting the line thickness and color.

        """
        hist, bin_edges = np.histogram(x, bins=bins, range=range,
                                       weights=weights, density=density)
        if self.axes is None:
            x_lim = _fixup_lim(x_lim, bin_edges)
            y_lim = _fixup_lim(y_lim, hist)
            self.draw_axes(
                x_lim, y_lim, width=width, height=height, margin=margin,
                border=border, padding=padding, style=style)
        self.axes.draw_histogram(hist, bin_edges, style=style)
        return self.axes

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

        style = self._check_style(style)
        lw = self.get_param('affine_lw', style)
        col = self.get_param('affine_line_col', style)

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
