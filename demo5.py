#! /usr/bin/env python3

import numpy as np

from jvplot import Plot

with Plot('demo5.pdf', '4.5in', '4.5in') as pl:
    ax = pl.viewport([pl.x, pl.y, pl.width, pl.height], (0, 1), (0, 1))

    w = 10
    h = 10
    img = np.random.uniform(size=(h, w, 3))
    img[:2, :3, :] = 1
    img[0, 1, :] = 0
    ax.draw_image([0, 0, 1, 1], img)
