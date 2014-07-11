#! /usr/bin/env python

import numpy as np

from jvplot import Plot

with Plot('demo2.pdf', '4in', '8in') as pl:
    t = np.linspace(0, 2*np.pi, 200)
    for i in range(4):
        subplot, _ = pl.subplot(1, 4, i)
        subplot.plot(t, np.sin((i+1)*t), smart=True)
