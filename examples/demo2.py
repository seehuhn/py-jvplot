#! /usr/bin/env python3

import numpy as np

from jvplot import Plot

with Plot('demo2.pdf', '4in', '8in') as pl:
    t = np.linspace(0, 2*np.pi, 200)
    for i in range(4):
        panel = pl.subplot(1, 4, i)
        ax = panel.plot(t, np.sin((4-i)*t))
        ax.draw_affine(y=0, style=dict(line_dash='1.5pt'))
        ax.draw_affine(x=0, style=dict(line_dash='1.5pt'))
        ax.draw_affine(x=np.pi, style=dict(line_dash='1.5pt'))
        ax.draw_affine(x=2*np.pi, style=dict(line_dash='1.5pt'))
