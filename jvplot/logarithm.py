#! /usr/bin/env python3

import numpy as np

def _main():
    a = 0.003
    b = 12

    n = 5
    steps = np.linspace(np.log10(a), np.log10(b), n)
    r = steps - np.floor(steps)
    print(r)

if __name__ == "__main__":
    _main()
