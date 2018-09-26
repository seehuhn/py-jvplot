#! /usr/bin/env python3

import numpy as np

import jvplot


n = 500
p = 4

m = np.random.standard_normal(size=p)
A = np.random.standard_normal(size=(p, p))
x = np.random.standard_normal(size=(n, p)) @ A + m

style = {
    'margin_left': '7mm',
    'margin_right': '7mm',
    'margin_top': '7mm',
    'margin_bottom': '7mm',
    'margin_between': '3mm',
    'axis_tick_length': '1mm',
    'axis_ticks': 'BLTR',
}
with jvplot.Plot("demo7.pdf", 6, 6, style=style) as pl:
    pl.pair_scatter_plot(x, diag_fn="blank")
