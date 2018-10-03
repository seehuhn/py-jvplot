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
        dim: The dimension, either as a number (device units) or a
            dimension string including a unit (e.g. "1cm").
        res: The device resolution in units/inch.
        parent_length: The length of the surrounding element in device
            units.  If this is set, relative lengths (e.g. "50%") are
            allowed.

    Returns:
        How many device units correspond to `dim`.

    """
    if dim is None:
        return None

    unit = None

    try:
        dim = float(dim)
        unit = 1
    except:
        dim = str(dim)

    if unit is None:
        for pfx, scale in UNITS.items():
            if dim.endswith(pfx):
                dim = dim[:-len(pfx)]
                unit = scale * res
                break

    if unit is None and dim.endswith('px'):
        if res is None:
            raise ValueError(f'pixel length {dim} in invalid context')
        dim = dim[:-2]
        unit = 1

    if unit is None and dim.endswith('%'):
        if parent_length is None:
            raise ValueError(
                'relative length %s in invalid context' % dim)
        dim = dim[:-1]
        unit = parent_length / 100

    if unit is None:
        raise ValueError(f"invalid dimension {dim!r}")

    return float(dim) * unit

def parse_dash_pattern(dash, res):
    if not dash or dash == "none":
        return []
    lengths = dash.split(",")
    return [convert_dim(l, res) for l in lengths]

def check_vec(v, n, broadcast=False):
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
    if k != n:
        tmpl = "%s used as vec%d, but has length %s != %d"
        raise ValueError(tmpl % (repr(v), n, k, n))
    return v


def _check_num_vec(v, n, broadcast=False):
    v = check_vec(v, n, broadcast)
    try:
        v = [float(vi) for vi in v]
    except ValueError:
        raise TypeError(
            "%s used as numeric vector, but has non-numeric entries" % repr(v))
    return v


def _check_coords(x, y):
    x = np.array(x)
    if not x.shape:
        x = x.reshape((1,))
    if y is None:
        shape = x.shape
        if len(shape) == 1:
            return np.arange(1, shape[0]+1), x
        if len(shape) == 2 and shape[1] == 2:
            return x[:, 0], x[:, 1]
        raise ValueError('x has wrong shape %s' % shape)
    y = np.array(y)
    if not y.shape:
        y = y.reshape((1,))
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

def data_range(*args):
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
