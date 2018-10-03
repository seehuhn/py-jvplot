# util_test.py - unit tests for util.py
# Copyright (C) 2014 Jochen Voss <voss@seehuhn.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import pytest

import numpy as np

from . import util


def testconvert_dim():
    for res in [50, 72, 100]:
        tests = [
            ('1in', 1),
            ('2.54cm', '1in'),
            ('10mm', '1cm'),
            ('72bp', '1in'),
            ('72.27pt', '1in'),
            ('1pt', 1/72.27),
            ('1px', 1/res),
        ]
        print('\nres =', res)
        for a, b in tests:
            da = util.convert_dim(a, res)
            db = util.convert_dim(b, res)
            print(a, b, res)
            assert da == pytest.approx(db)

        d = util.convert_dim(1, res)
        assert d == pytest.approx(res)

def test_data_range():
    with pytest.raises(ValueError):
        util.data_range()

    a, b = util.data_range(1)
    assert a == 1 and b == 1

    a, b = util.data_range(3, 1, 4, 1, 5)
    assert a == 1 and b == 5

    a, b = util.data_range([3, 1, 4, 1, 5])
    assert a == 1 and b == 5

    a, b = util.data_range([1, (2, 3)],
                           [4, 5, 6],
                           np.arange(7, 10))
    assert a == 1 and b == 9

    a, b = util.data_range(np.inf, -np.inf, 2, np.nan)
    assert a == 2 and b == 2

    a, b = util.data_range([np.inf, -np.inf, 2, np.nan])
    assert a == 2 and b == 2

    a, b = util.data_range(np.array([np.inf, -np.inf, 2, np.nan]))
    assert a == 2 and b == 2

    with pytest.raises(TypeError):
        util.data_range("fish")
