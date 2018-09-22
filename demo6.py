#! /usr/bin/env python3

import numpy as np

from jvplot import Plot

w = 100
h = 80
x = np.linspace(0, 10, w)
y = np.linspace(0, 8, h)
d = np.square(np.expand_dims(x - 7, 0)) + np.square(np.expand_dims(y - 1, 1))

img = 1 - np.exp(-d)
img = np.transpose(np.array([img, img ** 2, 1 - img ** 3]), (1, 2, 0))
assert img.shape == (h, w, 3)

img[0, :, 0] = 0
img[h-1, :, 0] = 0
img[:, 0, 0] = 0
img[:, w-1, 0] = 0

with Plot('demo6.png', '6in', '4in') as pl:
    pl.image(img, (0, 10), (0, 8), aspect=1)
