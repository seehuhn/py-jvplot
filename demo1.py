#! /usr/bin/env python3

import numpy as np

from jvplot import Plot

with Plot('demo1.pdf', '4.5in', '4.5in') as fig:
    fig.scatter_plot(np.random.rand(100),
                     np.random.rand(100),
                     aspect=1,
                     margin="1cm")
