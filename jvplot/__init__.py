# __init__.py - package directory file for JvPlot
# Copyright (C) 2014-2018 Jochen Voss <voss@seehuhn.de>
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

"""A Simple Library for Creating Plots Programmatically
====================================================

:copyright: 2014, Jochen Voss
:license: GPL version 3 or newer, see LICENSE for more details

Quick Start
-----------

The main entry point for the JvPlot package is the
:py:class:`jvplot.plot.Plot()` class which creates a new figure.  The
name :py:func:`jvplot.Plot()` can be used as a shorthand for
:py:class:`jvplot.plot.Plot()`.

Modules
-------

The JvPlot package is composed of the following main modules:

* :py:mod:`jvplot.plot`
* :py:mod:`jvplot.axes`
* :py:mod:`jvplot.canvas`
* :py:mod:`jvplot.param`

"""

__title__ = 'jvplot'
__version__ = '0.3'
__author__ = 'Jochen Voss'
__license__ = 'GPLv3+'
__copyright__ = 'Copyright (c) 2014-2018 Jochen Voss'

from .plot import Plot
