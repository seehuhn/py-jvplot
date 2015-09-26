#! /usr/bin/env python3

import cairocffi as cairo

w = 450
h = 200

font_size = 72

surface = cairo.PDFSurface("tryfont.pdf", w, h)
ctx = cairo.Context(surface)
ctx.translate(0, h)
ctx.scale(1, -1)
ctx.set_font_matrix(cairo.Matrix(font_size, 0, 0, -font_size, 0, 0))

ascent, descent, _, _, _ = ctx.font_extents()

x = 20
y = 40

ctx.set_line_width(0.5)
ctx.move_to(0, y)
ctx.line_to(w, y)
ctx.move_to(0, y+ascent)
ctx.line_to(w, y+ascent)
ctx.move_to(0, y-descent)
ctx.line_to(w, y-descent)
ctx.stroke()

ctx.move_to(x, y)
ctx.show_text("gate (plonk)")

surface.finish()
