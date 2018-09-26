#! /usr/bin/env python3

import cairocffi as cairo

font_size = 72
lines = [
    "(line before)",
    "plonk",
    " o o o",
    "(line after)",
]
w = 450
h = 400

surface = cairo.PDFSurface("tryfont.pdf", w, h)
ctx = cairo.Context(surface)
ctx.translate(0, h)
ctx.scale(1, -1)

ctx.set_font_matrix(cairo.Matrix(font_size, 0, 0, -font_size, 0, 0))
ascent, descent, baseline_skip, _, _ = ctx.font_extents()
if baseline_skip < descent+ascent + 3:
    print("slightly increased line spacing")
    baseline_skip = descent + ascent + 3

ctx.set_line_width(0.5)

x = 20
for k, text in enumerate(lines):
    y = h - 20 - ascent - k * baseline_skip

    ctx.save()
    ctx.set_source_rgb(.9, .9, .9)
    ctx.rectangle(0, y-descent, w, ascent+descent)
    ctx.fill()
    ctx.restore()

    x_bearing, y_bearing, box_w, box_h, dx, dy = ctx.text_extents(text)

    ctx.rectangle(x+x_bearing, y+y_bearing, box_w, box_h)
    ctx.save()
    ctx.set_source_rgb(.8, .8, .8)
    ctx.fill()
    ctx.restore()
    ctx.stroke()

    ctx.move_to(0, y)
    ctx.line_to(w, y)
    ctx.move_to(0, y+ascent)
    ctx.line_to(w, y+ascent)
    ctx.move_to(0, y-descent)
    ctx.line_to(w, y-descent)
    ctx.stroke()

    ctx.move_to(x, y)
    ctx.show_text(text)

    ctx.save()
    ctx.set_source_rgb(.8, 0, 0)
    ctx.set_line_width(5)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x, y)
    ctx.line_to(x, y)
    ctx.move_to(x+dx, y+dy)
    ctx.line_to(x+dx, y+dy)
    ctx.stroke()
    ctx.restore()

surface.finish()
