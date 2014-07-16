import math
import numpy as np

_q = 10**0.25 / 2

def _axis_tick_distance(k):
    c = [1.0, 2.0, 2.5, 5.0][k%4]
    return c * 10**(k//4)

def _next_axis_tick(x):
    k = math.floor(math.log10(_q * x) * 4)
    d = _axis_tick_distance(k)
    return k if d > x else k+1
