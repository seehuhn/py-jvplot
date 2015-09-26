#! /usr/bin/env python3

import itertools

import numpy as np

import jvplot

plot_no = itertools.count(1)


def line_plot():
    fig = yield ("line", 5, 5)
    t = np.linspace(0, 2*np.pi, 200)
    fig.plot(t, np.sin(t))


def scatter_plot():
    fig = yield ("scatter", 5, 5)
    fig.scatter_plot(np.random.rand(1000),
                     np.random.rand(1000),
                     aspect=1)

plot_fns = [fn for name, fn in globals().items() if name.endswith('_plot')]
for fn in plot_fns:
    for ext in ['pdf', 'png']:
        fnx = fn()
        name, width, height = next(fnx)
        plot_name = "test-%03d-%s.%s" % (next(plot_no), name, ext)
        with jvplot.Plot(plot_name, width, height) as fig:
            try:
                fnx.send(fig)
            except StopIteration:
                pass
