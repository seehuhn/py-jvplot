# device.py - handle JvPlot graphics devices
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

"""The Device class
----------------

The `Device` class keeps track of grpahics parameters and provides
support for drawing text.

"""

import numpy as np

import cairocffi as cairo

from . import color
from . import errors
from . import param
from . import util


class Device:

    """A graphics device to draw a plot on.

    This class is only used as a base class for :py:class:`Canvas` and
    :py:class:`axes.Axes`.  The ``Device`` class itself is not normally
    instantiated.

    This class keeps track of the resolution and dimensions of the
    drawing area, and of the graphical style parameters.

    """

    def __init__(self, ctx, rect, *, res, parent=None, style=None):
        """Create a new Device object.

        Args:
            ctx ():
            rect ():
            res ():
            parent ():
            style ():

        """
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

    def get_param(self, key, *, style=None):
        """Get the value of graphics parameter ``key``.

        If the optional argument ``style`` is given, it must be a
        dictionary, mapping parameter names to values; in this case,
        values in ``style`` override values set in the Canvas object.

        Args:
            key (string): the graphics parameter name to query.
            style (dict): graphics parameter values to override the
                canvas settings.

        """
        style = param.check_keys(style)
        return self._get_param(key, style)

    def _get_param(self, key, style, use_default=False):
        seen = [key]
        while True:
            value = style.get(key)
            if value is None and use_default:
                value = param.DEFAULT.get(key, [None, None])[1]
            if value is None:
                value = self.style.get(key)
            if value is None:
                msg = f"invalid style parameter '{key}'"
                raise errors.InvalidParameterName(msg)

            if isinstance(value, str) and value.startswith('$'):
                key = value[1:]
                if key in seen:
                    msg = ' -> '.join(seen + [key])
                    raise errors.WrongUsage("infinite parameter loop: " + msg)
                seen.append(key)
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
            if value in (True, "yes", 1):
                return True
            if value in (False, "no", 0):
                return False
            raise ValueError(f"cannot use {value!r} as a bool")
        if info[0] == 'dash':
            return util.parse_dash_pattern(value, self.res)
        if info[0] == 'str':
            return str(value)
        raise NotImplementedError("parameter type '%s'" % info[0])

    def debug_style(self, *, style=None):
        keys = []
        vals = []
        defaults = []
        descs = []
        for key, (tp, default, desc) in param.DEFAULT.items():
            val = self._get_param(key, style=style)

            if tp == "col":
                r, g, b, a = val
                r2, g2, b2 = int(r*255+.5), int(g*255+.5), int(b*255+.5)
                try_names = [n for n, c in color.names.items() if c == (r2, g2, b2)]
                if a == 0:
                    val = "transparent"
                elif a == 1 and try_names:
                    val = try_names[0]
                elif a == 1:
                    val = f"rgb({r2},{g2},{b2})"
                else:
                    val = f"rgba({r2},{g2},{b2},{a:g})"
            elif tp in ["dim", "width", "height"]:
                val = f"{val/self.res*72.27:.1f}pt"

            keys.append(key)
            vals.append(str(val))
            defaults.append(str(default))
            descs.append(desc)

        ll = [max(len(s) for s in ss) for ss in [keys, vals, defaults, descs]]
        ll0 = ll[:-1] + [0]
        def p(fields):
            print(" | ".join("%-*s" % (l, f) for l, f in zip(ll0, fields)))

        print()
        p(["key", "value", "default", "description"])
        print("-+-".join("-"*l for l in ll))
        for fields in zip(keys, vals, defaults, descs):
            p(fields)


    def get_margin_rect(self, *, style=None):
        """Return the rectangle `[x, y, w, h]` defined by the margin graphics
        parameters, in device coordinates.

        Args:
            style ():

        """
        style = param.check_keys(style)
        return self._get_margin_rect(style)

    def _get_margin_rect(self, style):
        margin_bottom = self._get_param('margin_bottom', style)
        margin_left = self._get_param('margin_left', style)
        margin_top = self._get_param('margin_top', style)
        margin_right = self._get_param('margin_right', style)
        x = self.rect[0] + margin_left
        y = self.rect[1] + margin_bottom
        w = self.rect[2] - margin_left - margin_right
        h = self.rect[3] - margin_bottom - margin_top
        if w < 0 or h < 0:
            raise ValueError("not enough space, margins too large")
        return [x, y, w, h]

    def text_width(self, text, font_size):
        """Returns the width of the text's bounding box.

        Args:
            text ():
            font_size ():

        """
        self.ctx.save()
        self.ctx.set_font_matrix(
            cairo.Matrix(font_size, 0, 0, -font_size, 0, 0))
        ext = self.ctx.text_extents(text)
        self.ctx.restore()
        return ext[2]

    def font_height(self, font_size):
        """Returns the height of the tallest character in the font.

        Args:
            font_size ():

        """
        self.ctx.save()
        self.ctx.set_font_matrix(
            cairo.Matrix(font_size, 0, 0, -font_size, 0, 0))
        ext = self.ctx.font_extents()
        self.ctx.restore()
        return ext[0] + ext[1]

    def _draw_text(self, x, y, text, font_size, *, col=None, bg_col=None,
                   horizontal_align="start", vertical_align="baseline",
                   rotate=0, padding=["1pt", "3pt"], ctx=None):
        padding = util.check_vec(padding, 4, True)
        p_top = util.convert_dim(padding[0], self.res, self.rect[3])
        p_right = util.convert_dim(padding[1], self.res, self.rect[2])
        p_bottom = util.convert_dim(padding[2], self.res, self.rect[3])
        p_left = util.convert_dim(padding[3], self.res, self.rect[2])

        lines = text.splitlines()
        baseline_skip = 1.2 * font_size

        ctx = ctx or self.ctx
        ctx.save()
        ctx.set_font_matrix(
            cairo.Matrix(font_size, 0, 0, -font_size, 0, 0))

        ascent, descent, line_height, _, _ = ctx.font_extents()
        if vertical_align == "baseline":
            y_offs = 0
        elif vertical_align == "top":
            y_offs = -ascent
        elif vertical_align == "bottom":
            y_offs = descent
        elif vertical_align == "center":
            y_offs = (descent - ascent) / 2 + (len(lines) - 1) * baseline_skip / 2
        else:
            y_offs = util.convert_dim(vertical_align, self.res, line_height)

        for i, line in enumerate(lines):
            ext = ctx.text_extents(line)
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
                x_offs = util.convert_dim(horizontal_align, self.res, ext[2])

            if bg_col is not None and bg_col[3] > 0:
                ctx.save()
                ctx.set_source_rgba(*bg_col)
                ctx.move_to(x, y)
                ctx.rotate(rotate)
                ctx.rel_move_to(ext[0] + x_offs - p_left,
                                ext[1] + y_offs - p_bottom)
                ctx.rel_line_to(ext[2] + p_left + p_right, 0)
                ctx.rel_line_to(0, ext[3] + p_bottom + p_top)
                ctx.rel_line_to(- ext[2] - p_right - p_left, 0)
                ctx.close_path()
                ctx.fill()
                ctx.restore()
            if col:
                ctx.set_source_rgba(*col)

            ctx.move_to(x, y)
            ctx.rotate(rotate)
            ctx.rel_move_to(x_offs, y_offs)
            ctx.show_text(line)

            y_offs -= baseline_skip

        ctx.restore()

    @staticmethod
    def data_range(*args):
        """Determine the range of all (finite) values in `args`.

        Args:
            *args: All arguments are flattened.  The flattened version
                must consists of numeric values, and the range of the
                collection of all these numbers is returned.

        """
        lower = np.inf
        upper = -np.inf
        for arg in args:
            # ignore default values for unset parameters
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
                aa = np.array(arg).flatten()
                aa = aa[np.isfinite(aa)]
                a = np.min(aa)
                b = np.max(aa)
            except (ValueError, TypeError):
                a = None
            if a is not None:
                if a < lower:
                    lower = a
                if b > upper:
                    upper = b
                continue

            if not isinstance(arg, str):
                # try whether `arg` is iterable
                try:
                    for a2 in arg:
                        a, b = Device.data_range(a2)
                        if a < lower:
                            lower = a
                        if b > upper:
                            upper = b
                    continue
                except TypeError:
                    pass
            raise TypeError(f"invalid data range {arg!r}")

        if lower > upper:
            raise ValueError("no data range specified")
        return lower, upper
