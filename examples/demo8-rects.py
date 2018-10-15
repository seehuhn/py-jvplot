#! /usr/bin/env python3

import numpy as np

import jvplot

with jvplot.Plot("demo8-rects.pdf", "6in", "6in") as pl:
    ax = pl.axes(x_range=[0, 4], y_range=[0, 4], aspect=1)

    S = {
        'rect_bg': 'yellow',
        'rect_fg': 'red',
        'rect_lw': '1mm',
    }
    ax.draw_affine(x=0)
    ax.draw_affine(x=1)
    ax.draw_affine(x=2)
    ax.draw_affine(x=3)
    ax.draw_affine(x=4)
    ax.draw_affine(y=0)
    ax.draw_affine(y=1)
    ax.draw_affine(y=2)
    ax.draw_affine(y=3)
    ax.draw_affine(y=4)

    ax.draw_rectangle([
        [0.1, .1, .8, .8],
        [0.1, 3.1, .8, .8],
        [1.1, 1.9, .8, -np.inf],
        [1.9, 2.1, -np.inf, .8],
        [2.1, 1.1, np.inf, .8],
        [2.1, 2.1, .8, np.inf],
        [3.1, .1, .8, .8],
        [3.1, 3.1, .8, .8],
    ], style=S)
