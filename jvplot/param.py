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
    'axis.tick_width': ('dim', '$lw.medium', 'line width for axes tick marks'),
    'h_axis.tick_width': ('width', '$axis.tick_width', 'line width for tick marks on horizontal axes'),
    'v_axis.tick_width': ('height', '$axis.tick_width', 'line width for tick marks on vertical axes'),
    'lw': ('dim', '$lw.medium', 'line width'),
    'lw.medium': ('dim', '.8pt', 'default width for medium thick lines'),
    'lw.thick': ('dim', '1.2pt', 'default width for thick lines'),
    'lw.thin': ('dim', '.4pt', 'default width for thin lines'),
    'margin': ('dim', '2mm', 'default margin around the plotting area'),
    'margin.bottom': ('height', '$margin', 'margin below the plotting area'),
    'margin.left': ('width', '$margin', 'margin to the left of the plotting area'),
    'margin.right': ('width', '$margin', 'margin to the right of the plotting area'),
    'margin.top': ('height', '$margin', 'margin above the plotting area'),
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
