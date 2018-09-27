#! /usr/bin/env python3

import numpy as np

import jvplot

w = 100
h = 80
x = np.linspace(0, 10, w)
y = np.linspace(0, 8, h)
d = np.square(np.expand_dims(x - 7, 0)) + np.square(np.expand_dims(y - 1, 1))
z = 1 / (1 + d)

cs = jvplot.color.Scale(
    ["blue", "purple", "red", "orange", "yellow"], z,
    smooth=.001)
img = cs(z)

assert img.shape == (h, w, 3)

img[0, :, 0] = 0
img[h-1, :, 0] = 0
img[:, 0, 0] = 0
img[:, w-1, 0] = 0

with jvplot.Plot('demo6.png', '6in', '4in') as pl:
    pl.color_bar(cs)
    pl.image(img, (0, 10), (0, 8), aspect=1)
