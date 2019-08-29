#! /usr/bin/env python3

import numpy as np
import pandas as pd

import jvplot


# load model outputs and ranges from ice core data
data = pd.read_csv('outputs.csv')
data = data.dropna()
ranges = pd.read_csv('ranges.csv')

# select required columns in the correct order (leaving out Renland)
names = ["NEEM", "NGRIP", "GRIP", "GISP2", "camp", "DYE3"]
data = data[names]
ranges = ranges[names]

# convert to numpy arrays
data = np.array(data)
ranges = np.array(ranges)

p = data.shape[1]
rr = [np.min(data), np.max(data)]

def scatter(pl, row, col, rect, x_range, y_range, style):
    ax = pl.axes(x_lim=x_range, y_lim=y_range, rect=rect, style=style)

    x_low, x_mid, x_high = ranges[:, col]
    y_low, y_mid, y_high = ranges[:, row]
    S = {
        'rect_bg': 'rgba(255,0,0,.2)',
        'rect_lw': 0,
    }
    ax.draw_rectangle([[None, y_low, None, y_high - y_low],
                       [x_low, None, x_high - x_low, None]],
                      style=S)
    ax.draw_rectangle([x_low, y_low, x_high - x_low, y_high - y_low],
                      style=S)

    S0 = {
        'plot_point_col': 'rgba(0,0,0,.3)',
        'plot_point_size': '4pt',
    }
    ax.draw_points(data[:, col], data[:, row], style=S0)

    S1 = {
        'plot_point_col': 'black',
        'plot_point_size': '1pt',
    }
    ax.draw_points(data[:, col], data[:, row], style=S1)

def label(pl, row, col, rect, x_range, y_range, style):
    plain = {
        'axis_border_lw': 0,
        'axis_ticks': '',
    }
    name = names[col]
    if name == "camp":
        name = "Camp\nCentury"
    ax = pl.axes(x_lim=[0, 1], y_lim=[0, 1], rect=rect, style=plain)
    ax.draw_text(name, .5, .5,
                 horizontal_align='center', vertical_align='center')

S0 = {
    'axis_border_lw': '.8pt',
    'axis_col': '#777',
    'axis_tick_length': '1.5pt',
    'axis_tick_lw': '.5pt',
    'axis_tick_spacing_x': '2mm',
    'axis_tick_spacing_y': '0.1mm',
    'axis_ticks': 'BLTR',
    'tick_font_size': '6pt',
    'margin_bottom': '3mm',
    'margin_left': '3mm',
    'margin_top': '3mm',
    'margin_right': '3mm',
    'padding': '1pt',
}
with jvplot.Plot('demo9.pdf', '5.5in', '5.5in') as pl:
    pl.grid_plot([rr]*p, x_names=names,
                 upper_fn=scatter, diag_fn=label, lower_fn=scatter,
                 style=S0)
