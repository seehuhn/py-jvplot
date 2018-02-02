# util.py - auxiliary functions for JvPlot
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

import numpy as np

UNITS = {
    'in': 1,
    'cm': 1 / 2.54,
    'mm': 1 / 25.4,
    'bp': 1 / 72,
    'pt': 1 / 72.27,
}


def convert_dim(dim, res, parent_length=None):
    """Convert dimensions to device coordinates.

    Args:
        dim: The dimension either a number (inches) or a dimension
            string including a unit (e.g. "1cm").
        res: The device resolution in units/inch.
        parent_length: The length of the surrounding element in
            inches.  If this is set, relative lengths (e.g. "50%") are
            allowed.

    """
    if dim is None:
        return None
    unit = 1
    try:
        for pfx, scale in UNITS.items():
            if not dim.endswith(pfx):
                continue
            dim = dim[:-len(pfx)]
            unit = scale
        else:
            if dim.endswith('px'):
                if res is None:
                    raise ValueError(
                        'pixel length %s in invalid context' % dim)
                dim = dim[:-2]
                unit = 1 / res
            elif dim.endswith('%'):
                if parent_length is None:
                    raise ValueError(
                        'relative length %s in invalid context' % dim)
                dim = dim[:-1]
                unit = parent_length / 100 / res
    except AttributeError:
        pass
    return float(dim) * unit * res


def _check_vec(v, n, broadcast=False):
    if isinstance(v, str):
        if not broadcast:
            raise TypeError('string "%s" used as vec%d' % (v, n))
        return [v] * n
    try:
        k = len(v)
    except TypeError:
        if not broadcast:
            tmpl = "%s used as vec%d, but does not have a length"
            raise TypeError(tmpl % (repr(v), n))
        k = 1
        v = [v]

    if broadcast and 1 <= k < n and n % k == 0:
        return list(v) * (n // k)
    elif k != n:
        tmpl = "%s used as vec%d, but has length %s != %d"
        raise ValueError(tmpl % (repr(v), n, k, n))
    return v


def _check_num_vec(v, n, broadcast=False):
    v = _check_vec(v, n, broadcast)
    try:
        v = [float(vi) for vi in v]
    except ValueError:
        raise TypeError(
            "%s used as numeric vector, but has non-numeric entries" % repr(v))
    return v


def _check_range(r):
    r = _check_num_vec(r, 2)
    if not r[0] < r[1]:
        raise ValueError("invalid range %s" % repr(r))
    return r


def _check_coords(x, y):
    x = np.array(x)
    if y is None:
        shape = x.shape
        if len(shape) == 1:
            return np.arange(1, shape[0]+1), x
        elif len(shape) == 2 and shape[1] == 2:
            return x[:, 0], x[:, 1]
        else:
            raise ValueError('x has wrong shape %s' % shape)
    else:
        y = np.array(y)
    if len(x.shape) != 1:
        raise ValueError('x has wrong shape %s' % repr(x.shape))
    if len(y.shape) != 1:
        raise ValueError('y has wrong shape %s' % repr(y.shape))
    if len(x) != len(y):
        tmpl = 'x and y have incompatible length: %d != %d'
        raise ValueError(tmpl % (len(x), len(y)))
    return x, y


def _check_coord_pair(x, y):
    if y is None:
        x, y = list(x)
    return float(x), float(y)
