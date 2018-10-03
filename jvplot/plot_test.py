#! /usr/bin/env python3

import pytest

from . import plot

def test_plot_size():
    no_padding = {
        'padding': 0,
    }
    with plot.Plot("/dev/null", "5in", "3in", style=no_padding) as pl:
        _, _, w, h = pl.rect
        assert w == pytest.approx(5 * pl.res)
        assert h == pytest.approx(3 * pl.res)
    with plot.Plot("/dev/null", 500, 300, style=no_padding) as pl:
        _, _, w, h = pl.rect
        assert w == pytest.approx(500)
        assert h == pytest.approx(300)

def test_plot_str():
    with plot.Plot("/dev/null", "5in", "3in") as pl:
        s = str(pl)
        assert "/dev/null" in s
