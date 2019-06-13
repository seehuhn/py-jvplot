#! /usr/bin/env python3

from . import layout, scale

def test_layout_2d():
    s = scale.Linear()
    lx = layout.Layout(520, 10, (0.9, 2.2),
                       lim=(0, 3),
                       dev_opt_dist=100,
                       dev_width_fn=lambda s: 5*len(s),
                       can_shift=True,
                       scale=s)
    ly = layout.Layout(320, 10, (-0.1, 0.9),
                       dev_opt_dist=100,
                       dev_width_fn=lambda s: 9,
                       scale=s)
    l = layout.Layout2D(lx, ly)
    l.fix(aspect=0.1)

    print()
    print(lx.ticks)
    print(lx.labels)

    print(ly.ticks)
    print(ly.labels)
