#! /usr/bin/env python

import numpy as np

from jvplot import Plot

style = dict(plot_lw='4pt')
with Plot('demo4.pdf', '4.5in', '4.5in', style=style) as pl:
    pl.set_limits((0, 1), (0, 1))
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
    pl.draw_lines(coords)
