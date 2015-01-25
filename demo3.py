#! /usr/bin/env python3

import numpy as np

from jvplot import Plot

with Plot('demo3.pdf', '4.5in', '4.5in') as pl:
    x = np.random.rand(10000) ** 2
    pl.histogram(x, bins=30)
