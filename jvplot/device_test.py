#! /usr/bin/env python3

import pytest

import numpy as np

from . import param, plot


def test_get_param_bool():
    key = 'plot_point_separate'
    assert param.DEFAULT[key][0] == 'bool'
    with plot.Plot('/dev/null', 100, 100) as pl:
        cases = [
            (True, True),
            ('yes', True),
            (1, True),
            (False, False),
            ('no', False),
            (0, False),
        ]
        for val, res in cases:
            style = {
                key: val,
            }
            assert pl.get_param(key, style=style) == res
        with pytest.raises(ValueError):
            style = {
                key: 'maybe',
            }
            pl.get_param(key, style=style)

def test_data_range():
    data_range = plot.Plot.data_range

    with pytest.raises(ValueError):
        data_range()

    a, b = data_range(1)
    assert a == 1 and b == 1

    a, b = data_range(3, 1, 4, 1, 5)
    assert a == 1 and b == 5

    a, b = data_range([3, 1, 4, 1, 5])
    assert a == 1 and b == 5

    a, b = data_range([1, (2, 3)],
                           [4, 5, 6],
                           np.arange(7, 10))
    assert a == 1 and b == 9

    a, b = data_range(np.inf, -np.inf, 2, np.nan)
    assert a == 2 and b == 2

    a, b = data_range([np.inf, -np.inf, 2, np.nan])
    assert a == 2 and b == 2

    a, b = data_range(np.array([np.inf, -np.inf, 2, np.nan]))
    assert a == 2 and b == 2

    with pytest.raises(TypeError):
        data_range("fish")
