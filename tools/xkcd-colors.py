#! /usr/bin/env python3

import urllib.request

print("colors = {")
with urllib.request.urlopen('http://xkcd.com/color/rgb.txt') as f:
    for l in f.read().decode('ASCII').splitlines():
        if l.startswith('#'):
            continue
        name, hex = l.split('#')
        r = int(hex[0:2], 16)
        g = int(hex[2:4], 16)
        b = int(hex[4:6], 16)
        print("    '%s': (%d, %d, %d)," % (name.strip(), r, g, b))
print("}")
