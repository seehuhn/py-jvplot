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
    'affine_line_col': ('col', '$line_col', 'default line color for straight lines'),
    'affine_lw': ('dim', '$lw', 'default line width for straight lines'),
    'axis_border': ('dim', '$lw_thick', 'axis line width'),
    'axis_font_size': ('dim', '$font_size', 'font size for axis tick labels'),
    'axis_label_dist': ('dim', '3pt', 'default distance between tick labels and tick marks'),
    'axis_label_font_size': ('dim', '$font_size', 'font size for axis labels'),
    'axis_label_sep': ('dim', '6pt', 'minimum separation of axis labels'),
    'axis_lw': ('dim', '$lw_thick', 'line width of the axis boxes'),
    'axis_margin_bottom': ('height', '7mm', 'default axis bottom margin'),
    'axis_margin_left': ('width', '14mm', 'default axis left margin'),
    'axis_margin_right': ('width', '2mm', 'default axis right margin'),
    'axis_margin_top': ('height', '2mm', 'default axis top margin'),
    'axis_padding': ('dim', '2mm', 'default axis padding'),
    'axis_padding_bottom': ('height', '$axis_padding', 'default axis bottom padding'),
    'axis_padding_left': ('width', '$axis_padding', 'default axis left padding'),
    'axis_padding_right': ('width', '$axis_padding', 'default axis right padding'),
    'axis_padding_top': ('height', '$axis_padding', 'default axis top padding'),
    'axis_tick_length': ('dim', '3pt', 'length of axis tick marks'),
    'axis_tick_opt_spacing': ('dim', '2cm', 'optimal spacing for axis tick marks'),
    'axis_tick_width': ('dim', '$lw_medium', 'line width for axis tick marks'),
    'axis_x_label_dist': ('dim', '$axis_label_dist', 'vertical distance between labels and tick marks on the x-axis'),
    'axis_y_label_dist': ('dim', '$axis_label_dist', 'horizontal distance between labels and tick marks on the y-axis'),
    'bg_col': ('col', 'transparent', 'background color'),
    'font_size': ('dim', '10pt', 'default font size'),
    'hist_col': ('col', '$line_col', 'line color for histogram boxes'),
    'hist_fill_col': ('col', '#CCC', 'default fill color for histogram bars'),
    'hist_lw': ('dim', '$lw_thin', 'default line width for histogram bars'),
    'line_col': ('col', 'black', 'default line color'),
    'lw': ('dim', '$lw_medium', 'line width'),
    'lw_medium': ('dim', '.8pt', 'default width for medium thick lines'),
    'lw_thick': ('dim', '1pt', 'default width for thick lines'),
    'lw_thin': ('dim', '.6pt', 'default width for thin lines'),
    'padding': ('dim', '2mm', 'default viewport padding'),
    'padding_bottom': ('height', '$padding', 'default viewport bottom padding'),
    'padding_left': ('width', '$padding', 'default viewport left padding'),
    'padding_right': ('width', '$padding', 'default viewport right padding'),
    'padding_top': ('height', '$padding', 'default viewport top padding'),
    'plot_col': ('col', '$line_col', 'default plot line color'),
    'plot_lw': ('dim', '$lw', 'default line width for plots'),
    'plot_point_col': ('col', '$line_col', 'default point color for scatter plots'),
    'plot_point_separate': ('bool', False, 'whether to draw points in a scatter plot individually'),
    'plot_point_size': ('dim', '2pt', 'point size for scatter plots'),
    'text_bg': ('col', 'rgba(255,255,255,.8)', 'default text background color'),
    'text_col': ('col', 'black', 'default text color'),
    'text_font_size': ('dim', '$font_size', 'default text font size'),
    'title_font_size': ('dim', '$font_size', 'font size for titles'),
    'title_top_margin': ('dim', '2mm', 'distance of title to top edge of canvas'),
}

VALID_KEYS = set(DEFAULT.keys())

ROOT = {
    'bg_col': 'white',
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
