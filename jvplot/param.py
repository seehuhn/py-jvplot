# param.py - configurable parameters for the jvplot package
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

from .util import _convert_dim

# name: (type, default, inherits from, description)
parameters = {
    'axis_font_size': ('dim', '$font_size', 'font size for axis labels'),
    'axis_label_dist': ('dim', '3pt', 'default distance between axis labels and tick marks'),
    'axis_lw': ('dim', '$lw_thick', 'line width of the axis boxes'),
    'axis_tick_length': ('dim', '3pt', 'length of axis tick marks'),
    'axis_tick_opt_spacing': ('dim', '2cm', 'optimal spacing for axis tick marks'),
    'axis_tick_width': ('dim', '$lw_medium', 'line width for axis tick marks'),
    'axis_x_label_dist': ('dim', '$axis_label_dist', 'vertical distance between labels and tick marks on the x-axis'),
    'axis_x_label_sep': ('dim', '8pt', 'minimum horizonal separation of x-axis labels'),
    'axis_y_label_dist': ('dim', '$axis_label_dist', 'horizontal distance between labels and tick marks on the y-axis'),
    'font_size': ('dim', '10pt', 'default font size'),
    'hist_lw': ('dim', '$lw', 'default line width for histogram bars'),
    'lw': ('dim', '$lw_medium', 'line width'),
    'lw_medium': ('dim', '.8pt', 'default width for medium thick lines'),
    'lw_thick': ('dim', '1pt', 'default width for thick lines'),
    'lw_thin': ('dim', '.6pt', 'default width for thin lines'),
    'margin': ('dim', '2mm', 'default margin around the plotting area'),
    'margin.bottom': ('height', '$margin', 'margin below the plotting area'),
    'margin.left': ('width', '$margin', 'margin to the left of the plotting area'),
    'margin.right': ('width', '$margin', 'margin to the right of the plotting area'),
    'margin.top': ('height', '$margin', 'margin above the plotting area'),
    'plot_lw': ('dim', '$lw', 'default line width for plots'),
    'plot_point_size': ('dim', '2pt', 'default point size for scatter plots'),
}

def get(name, res, style={}, parent_width=None, parent_height=None):
    while True:
        info = parameters.get(name)
        if info is None:
            raise ValueError('unknown parameter "%s"' % name)
        if name in style:
            value = style[name]
        else:
            value = info[1]
        if isinstance(value, str) and value.startswith('$'):
            name = value[1:]
        else:
            break
    if info[0] == 'width':
        return _convert_dim(value, res, parent_width)
    elif info[0] == 'height':
        return _convert_dim(value, res, parent_height)
    elif info[0] == 'dim':
        return _convert_dim(value, res)
    else:
        return value
