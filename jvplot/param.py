# param.py - default parameters for the jvplot package
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

from . import errors

# name: (type, default value, description)
DEFAULT = {
    'affine_line_col': ('col', '$line_col', 'line color for straight lines'),
    'affine_lw': ('dim', '$lw_thin', 'line width for straight lines'),
    'axis_border_col': ('col', 'inherit', 'axis border line color'),
    'axis_border_lw': ('dim', 'inherit', 'axis border line width'),
    'axis_col': ('col', 'inherit', 'default color for all parts of an axis'),
    'axis_label_col': ('col', 'inherit', 'color for axis labels'),
    'axis_label_dist_x': ('height', 'inherit', 'vertical distance of axis labels from x-axis'),
    'axis_label_dist_y': ('width', 'inherit', 'horizontal distance of axis labels from y-axis'),
    'axis_label_size': ('dim', 'inherit', 'font size for axis labels'),
    'axis_labels': ('str', 'inherit', 'positions of axis labels'),
    'axis_tick_col': ('col', 'inherit', 'axis tick line color'),
    'axis_tick_length': ('dim', 'inherit', 'length of axis tick marks'),
    'axis_tick_opt_spacing': ('dim', '2cm', 'optimal spacing for axis tick marks'),
    'axis_tick_width': ('dim', 'inherit', 'line width for axis tick marks'),
    'axis_ticks': ('str', 'inherit', 'positions of axis ticks and tick labels'),
    'color_bar_width': ('width', '21pt', 'width of a color bar'),
    'color_bar_border_lw': ('dim', '$lw_thin', 'color bar border line width'),
    'fg_col': ('col', 'inherit', 'default foreground color'),
    'bg_col': ('col', 'transparent', 'background color'),
    'font_size': ('dim', '10pt', 'font size'),
    'hist_col': ('col', '$line_col', 'line color for histogram boxes'),
    'hist_fill_col': ('col', '#CCC', 'fill color for histogram bars'),
    'hist_lw': ('dim', '$lw_thin', 'line width for histogram bars'),
    'line_col': ('col', '$fg_col', 'line color'),
    'line_dash': ('dash', 'none', 'line dash pattern'),
    'lw': ('dim', '$lw_medium', 'line width'),
    'lw_medium': ('dim', '.8pt', 'width for medium thick lines'),
    'lw_thick': ('dim', '1pt', 'width for thick lines'),
    'lw_thin': ('dim', '.6pt', 'width for thin lines'),
    'margin_between': ('dim', '2mm', 'margin between axis boxes'),
    'margin_bottom': ('height', '11mm', 'axis bottom margin'),
    'margin_left': ('width', '14mm', 'axis left margin'),
    'margin_right': ('width', '2mm', 'axis right margin'),
    'margin_top': ('height', '2mm', 'axis top margin'),
    'padding': ('dim', '2.5mm', 'viewport padding'),
    'padding_bottom': ('height', '$padding', 'viewport bottom padding'),
    'padding_left': ('width', '$padding', 'viewport left padding'),
    'padding_right': ('width', '$padding', 'viewport right padding'),
    'padding_top': ('height', '$padding', 'viewport top padding'),
    'plot_col': ('col', '$line_col', 'plot line color'),
    'plot_lw': ('dim', '$lw', 'line width for plots'),
    'plot_point_col': ('col', 'inherit', 'point color for scatter plots'),
    'plot_point_separate': ('bool', False, 'whether to draw points in a scatter plot individually'),
    'plot_point_size': ('dim', 'inherit', 'point size for scatter plots'),
    'text_bg': ('col', 'rgba(255,255,255,.8)', 'text background color'),
    'text_col': ('col', '$fg_col', 'text color'),
    'text_font_size': ('dim', '$font_size', 'text font size'),
    'tick_font_col': ('col', '$axis_col', 'color for tick labels'),
    'tick_font_size': ('dim', '$font_size', 'font size for tick labels'),
    'tick_label_dist': ('dim', '3pt', 'distance between tick labels and tick marks'),
    'tick_label_dist_x': ('dim', '$tick_label_dist', 'vertical distance between tick labels and marks, for the x-axis'),
    'tick_label_dist_y': ('dim', '$tick_label_dist', 'horizontal distance between tick labels and marks, for the y-axis'),
    'title_font_size': ('dim', '$font_size', 'font size for titles'),
    'title_top_margin': ('dim', '2mm', 'distance of title to top edge of canvas'),
}

VALID_KEYS = set(DEFAULT.keys())

ROOT = {
    'axis_border_col': '$axis_col',
    'axis_border_lw': '$lw_thick',
    'axis_col': '#444',
    'axis_label_col': '$text_col',
    'axis_label_dist_x': '7mm',
    'axis_label_dist_y': '10mm',
    'axis_label_size': '$font_size',
    'axis_labels': 'bl',
    'axis_tick_col': '$axis_col',
    'axis_tick_length': '3pt',
    'axis_tick_width': '$lw_medium',
    'axis_ticks': 'BL',
    'bg_col': 'white',
    'fg_col': 'black',
    'plot_point_col': '$line_col',
    'plot_point_size': '2pt',
}

def check_keys(style):
    if style is None:
        return {}
    invalid = style.keys() - VALID_KEYS
    if invalid:
        msg = "invalid style parameter '%s'" % invalid.pop()
        raise errors.InvalidParameterName(msg)
    return style

def update(*styles, parent_style=None, **kwargs):
    """Merge a list of styles.

    Later entries override earlier ones and defaults are used where no
    values are given.

    """
    if kwargs:
        styles = styles + (kwargs,)
    styles = [dict(style) for style in styles if style is not None]

    for style in styles:
        check_keys(style)

    res = {}
    for key, (_, default, _) in DEFAULT.items():
        val = default
        for style in styles:
            if key in style:
                val = style[key]
        if val == "inherit":
            if parent_style is None:
                raise ValueError(f"no parent, cannot inherit style {key!r}")
            val = parent_style.get(key)
        assert val is not None and val != "inherit"
        res[key] = val
    return res

def merge(*styles, parent_style=None, **kwargs):
    res = {}
    for style in styles + (kwargs,):
        if style is None:
            continue
        for key, val in style.items():
            if key not in DEFAULT:
                raise ValueError(f"invalid style parameter {key!r}")
            if val == "inherit":
                if parent_style is None:
                    raise ValueError(f"cannot inherit style {key!r}, no parent")
                val = parent_style.get(key, DEFAULT[key][1])
            res[key] = val
    return res
