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
    'affine_lw': ('dim', '$lw', 'line width for straight lines'),
    'axis_border': ('dim', '$lw_thick', 'axis line width'),
    'axis_label_dist': ('dim', '3pt', 'distance between tick labels and tick marks'),
    'axis_label_sep': ('dim', '6pt', 'minimum separation of axis labels'),
    'axis_margin_between': ('dim', '2mm', 'margin between axis boxes'),
    'axis_margin_bottom': ('height', '10mm', 'axis bottom margin'),
    'axis_margin_left': ('width', '14mm', 'axis left margin'),
    'axis_margin_right': ('width', '2mm', 'axis right margin'),
    'axis_margin_top': ('height', '2mm', 'axis top margin'),
    'axis_tick_length': ('dim', '3pt', 'length of axis tick marks'),
    'axis_tick_opt_spacing': ('dim', '2cm', 'optimal spacing for axis tick marks'),
    'axis_tick_width': ('dim', '$lw_medium', 'line width for axis tick marks'),
    'axis_x_label_dist': ('dim', '$axis_label_dist', 'vertical distance between tick labels and marks on the x-axis'),
    'axis_y_label_dist': ('dim', '$axis_label_dist', 'horizontal distance between tick labels and marks on the y-axis'),
    'bg_col': ('col', 'transparent', 'background color'),
    'font_size': ('dim', '10pt', 'font size'),
    'hist_col': ('col', '$line_col', 'line color for histogram boxes'),
    'hist_fill_col': ('col', '#CCC', 'fill color for histogram bars'),
    'hist_lw': ('dim', '$lw_thin', 'line width for histogram bars'),
    'label_font_size': ('dim', '$font_size', 'font size for axis labels'),
    'label_font_col': ('col', '$text_col', 'color for axis labels'),
    'line_col': ('col', 'black', 'line color'),
    'lw': ('dim', '$lw_medium', 'line width'),
    'lw_medium': ('dim', '.8pt', 'width for medium thick lines'),
    'lw_thick': ('dim', '1pt', 'width for thick lines'),
    'lw_thin': ('dim', '.6pt', 'width for thin lines'),
    'padding': ('dim', '2mm', 'viewport padding'),
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
    'text_col': ('col', 'black', 'text color'),
    'text_font_size': ('dim', '$font_size', 'text font size'),
    'tick_font_size': ('dim', '$font_size', 'font size for tick labels'),
    'title_font_size': ('dim', '$font_size', 'font size for titles'),
    'title_top_margin': ('dim', '2mm', 'distance of title to top edge of canvas'),
}

VALID_KEYS = set(DEFAULT.keys())

ROOT = {
    'bg_col': 'white',
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

def update(*styles, parent_style=None):
    """Merge a list of styles.  Later entries override earlier ones."""
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
