#! /usr/bin/env python3

import numpy as np

from jvplot import Plot

with Plot('demo5.png', '4.5in', '4.5in') as pl:
    ax = pl.axes(x_lim=(0, 1), y_lim=(0, 1), rect=pl.rect,
                 style=dict(axis_border_lw=0, axis_ticks=''))

    w = 10
    h = 10
    img = np.random.uniform(size=(h, w, 3))
    img[:2, :3, :] = 1
    img[0, 1, :] = 0
    ax.draw_image(img)
