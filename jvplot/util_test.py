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

import nose.tools
from .util import convert_dim


def testconvert_dim():
    for res in [50, 72, 100]:
        tests = [
            ('1in', 1),
            ('2.54cm', '1in'),
            ('10mm', '1cm'),
            ('72bp', '1in'),
            ('72.27pt', '1in'),
            ('1px', 1/res),
        ]
        print('\nres =', res)
        for a, b in tests:
            da = convert_dim(a, res)
            db = convert_dim(b, res)
            print(a, b, res)
            nose.tools.assert_almost_equal(da, db)
