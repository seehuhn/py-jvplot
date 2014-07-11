#! /usr/bin/env python

import numpy as np

from jvplot import Plot

with Plot('test.pdf', '5in', '3in') as pl:
    pl.scatter_plot(np.random.rand(137),
                    col=(1, 0, 0), size='1mm')
