#! /usr/bin/env python3

import numpy as np

from jvplot import Plot

style = {
    'padding': 0,
    'axis_margin_bottom': '1cm',
    'axis_margin_left': '1cm',
    'axis_margin_top': '1cm',
    'axis_margin_right': '1cm',
}
with Plot('demo4.pdf', '4.5in', '4.5in', style=style) as pl:
    ax = pl.viewport(pl.rect, (0, 1), (0, 1))
    coords = [
        [ 0.1, 0.1 ],
        [ 0.1, 0.9 ],
        [ 0.4, 0.9 ],
        [ np.nan, 0.9 ],
        [ 0.5, 0.9 ],
        [ np.nan, 0.9 ],
        [ 0.6, 0.9 ],
        [ 0.9, 0.9 ],
        [ 0.9, 0.1 ],
    ]
    ax.draw_lines(coords, style={
        'lw': '4pt',
    })
