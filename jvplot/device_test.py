#! /usr/bin/env python3

import pytest

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
