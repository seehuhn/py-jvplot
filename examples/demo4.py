#! /usr/bin/env python3

import numpy as np

from jvplot import Plot

style = {
    'padding': 0,
    'margin_bottom': '1cm',
    'margin_left': '1cm',
    'margin_top': '1cm',
    'margin_right': '1cm',
}
with Plot('demo4.pdf', '4.5in', '4.5in', style=style) as pl:
    plain = dict(axis_border_lw=0,
                 axis_ticks="")
    ax = pl.axes(x_lim=(0, 1), y_lim=(0, 1), rect=pl.rect, style=plain)
    coords = [
        [0.1, 0.1],
        [0.1, 0.9],
        [0.4, 0.9],
        [np.nan, 0.9],
        [0.5, 0.9],
        [np.nan, 0.9],
        [0.6, 0.9],
        [0.9, 0.9],
        [0.9, 0.1],
    ]
    ax.draw_lines(coords, style=dict(lw='4pt'))
