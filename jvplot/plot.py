# plot.py - implementation of the Plot class
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

"""
The Plot Class
--------------

This module provides the main entry point for the JvPlot package.
"""

import os.path

import cairocffi as cairo

from . import canvas, util, param

class Plot(canvas.Canvas):

    """The Plot Class represents a file containing a single figure.

    """

    def __init__(self, file_name, width, height=None, *, res=None, style={}):
        """Create a new plot.

        Args:
            file_name (string): The name of the file the figure will be
                stored in.  Any previously existing file with this name
                will be overwritten.  The file name extension determines
                the file type.  Available file types are `.pdf`, `.ps`,
                `.eps` and `.png`.

            width: The figure width.  This can either be a number to give
                the width in device units (pixels), or a string including
                a length unit like "10cm".

            height: The figure height.  This can either be a number to
                give the height in device units (pixels), or a string
                including a length unit like "10cm".

            res (number, optional): For raster image formats, `res`
                specifies the device resolution in pixels per inch.

            style (dict, optional): Default plot graphics values for the
                figure.

        """

        self.file_name = file_name
        """The output file name, as given in the ``file_name`` argument of the
        ``plot.Plot`` constructor (read only)."""

        _, ext = os.path.splitext(file_name)
        if ext:
            ext = ext[1:]
        elif file_name == "/dev/null":
            ext = None
        else:
            raise ValueError('file name "%s" lacks an extension' % file_name)

        if height is None:
            if width == "A4":
                width = "210mm"
                height = "297mm"
                style = param.merge(dict(padding="15mm"), style)
            elif width == "A4r":
                width = "297mm"
                height = "210mm"
                style = param.merge(dict(padding="15mm"), style)
            else:
                height = width

        if res is None:
            if ext == 'png':
                res = 100
            else:
                res = 72
        if ext == 'png':
            base_res = res
        else:
            base_res = 72
        w = int(util.convert_dim(width, res) + 0.5)
        h = int(util.convert_dim(height, res) + 0.5)

        q = base_res / res
        w_dev = int(w * q + .5)
        h_dev = int(h * q + .5)
        if ext == 'pdf':
            surface = cairo.PDFSurface(file_name, w_dev, h_dev)
        elif ext == 'ps':
            surface = cairo.PSSurface(file_name, w_dev, h_dev)
        elif ext == 'eps':
            surface = cairo.PSSurface(file_name, w_dev, h_dev)
            surface.set_eps(True)
        elif ext == 'png':
            surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w_dev, h_dev)
        elif ext is None:
            surface = cairo.RecordingSurface(cairo.CONTENT_COLOR,
                                             (0, 0, w_dev, h_dev))
        else:
            raise ValueError('unsupported file type "%s"' % ext)
        ctx = cairo.Context(surface)

        # move the origin to the bottom left corner:
        ctx.scale(q, -q)
        ctx.translate(0, -h)

        super().__init__(ctx, [0, 0, w, h], res=res, style=style)
        self.surface = surface
        self.file_name = file_name
        self.file_type = ext

    def __str__(self):
        _, _, w, h = self.rect
        res = self.res
        return f'<jvplot.Plot {w/res}in × {h/res}in {self.file_name!r}>'

    def close(self):
        """Close the plot and write all outstanding changes to the file.  The
        ``Plot`` object cannot be used any more after this call.

        """
        super().close()
        if self.file_type == 'png':
            self.surface.write_to_png(self.file_name)
        else:
            self.surface.finish()
        self.surface = None
