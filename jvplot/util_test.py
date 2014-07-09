import nose.tools
from .util import _convert_dim

def test_convert_dim():
    for res in [50, 72, 100]:
        tests = [
            ('1in', 1),
            ('2.54cm', '1in'),
            ('10mm', '1cm'),
            ('72bp', '1in'),
            ('72.27pt', '1in'),
            ('1px', 1/res),
        ]
        for a, b in tests:
            da = _convert_dim(a, res)
            db = _convert_dim(b, res)
            print(a, b, res)
            nose.tools.assert_almost_equal(da, db)
