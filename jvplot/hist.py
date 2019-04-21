# hist.py - helper functions for drawing histograms
# Copyright (C) 2019 Jochen Voss <voss@seehuhn.de>
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

def FreedmanDiaconis(x):
    """Implements a variant of the Freedman-Diaconis rule.

    https://en.wikipedia.org/wiki/Freedman%E2%80%93Diaconis_rule"""
    n = x.size
    ppp = np.nanpercentile(x, [0, 25, 75, 100])
    bins = int(n**(1/3) * (ppp[3] - ppp[0]) / (ppp[2] - ppp[1]) / 10 + 0.5)
    if bins < 1:
        bins = 1
    elif bins > 50:
        bins = 50
    return bins

def guess_bins(x):
    u = np.unique(x)
    if u.size < 2:
        return 1
    elif u.size < 20:
        u_int = u.astype(np.int)
        if np.all(u == u_int):
            a = np.min(u_int)
            b = np.max(u_int)
            return np.linspace(a-.5, b+.5, num=b-a+2)
    return FreedmanDiaconis(x)
