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

from .canvas import Canvas
from .util import convert_dim


class Plot(Canvas):

    """The Plot Class repesents a file containing a single figure.

    Args:
        file_name (string): The name of the file the figure will be
            stored in.  Any previously existing file with this name
            will be overwritten.  The file name extension determines
            the file type.  Available file types are `.pdf`, `.ps`,
            `.eps` and `.png`.

        width: The figure width.  This can either be a number to give
            the width in inches, or a string including a length unit
            like "10cm".

        height: The figure height.  This can either be a number to
            give the height in inches, or a string including a length
            unit like "10cm".

        res (number, optional): For raster image formats, `res`
            specifies the device resolution in pixels per inch.

        style (dict, optional): Default plot graphics values for the
            figure.

    """

    def __init__(self, file_name, width, height, *, res=100, style={}):
        """Create a new plot."""

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

        if ext != 'png':
            res = 72
        w = convert_dim(width, res)
        h = convert_dim(height, res)
        if ext == 'pdf':
            surface = cairo.PDFSurface(file_name, w, h)
        elif ext == 'ps':
            surface = cairo.PSSurface(file_name, w, h)
        elif ext == 'eps':
            surface = cairo.PSSurface(file_name, w, h)
            surface.set_eps(True)
        elif ext == 'png':
            w = int(w + 0.5)
            h = int(h + 0.5)
            surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
        elif ext is None:
            surface = cairo.RecordingSurface(cairo.CONTENT_COLOR,
                                             (0, 0, w, h))
        else:
            raise ValueError('unsupported file type "%s"' % ext)
        ctx = cairo.Context(surface)

        # move the origin to the bottom left corner:
        ctx.translate(0, h)
        ctx.scale(1, -1)

        super().__init__(ctx, [0, 0, w, h], res=res, style=style)
        self.surface = surface
        self.file_name = file_name
        self.file_type = ext

    def __str__(self):
        return '<JvPlot %.0fbpx%.0fbp "%s">' % (self.width, self.height,
                                                self.file_name)

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
