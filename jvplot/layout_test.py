#! /usr/bin/env python3

from . import layout, scale

def test_layout_2d():
    s = scale.Linear()
    lx = layout.Layout(520, (10, 10), (90, 220),
                       lim=(0, 3),
                       dev_opt_dist=100,
                       dev_width_fn=lambda s: 5*len(s),
                       can_shift=True,
                       scale=s)
    ly = layout.Layout(320, (10, 10), (-0.1, 0.9),
                       dev_opt_dist=100,
                       dev_width_fn=lambda s: 9,
                       scale=s)
    l = layout.Layout2D(lx, ly)
    l.fix(aspect=300/500)

    print()
    print(lx.lim, lx.labels)
    print(ly.lim, ly.labels)
