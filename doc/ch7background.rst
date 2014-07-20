Implementation Details
++++++++++++++++++++++

This chapter contains information about generating plots which has
influenced the design of the JvPlot package, but which is not required
for use of the package.


Coordinate Systems
==================

JvPlot uses two different coordinate systems, *device coordinates* and
*data coordinates*.  These systems are described in the following two
sections.

Device Coordinates
------------------

Device coordinates describe positions in the output image.  The
coordinate value `(0, 0)` corresponds to the bottom left corner of the
image.  The first coordinate value corresponds to the horizontal axis
(increasing to the right), the second coordinate corresponds to the
vertical axis, increasing upwards.  The maximal coordinates are given
by the canvas :py:attr:`~jvplot.canvas.Canvas.w` and
:py:attr:`~jvplot.canvas.Canvas.h` attributes.

The device resolution :py:attr:`~jvplot.canvas.Canvas.res` specifies
how many device coordinate units correspond to one inch.  For PDF and
PostScript figures, the resolution is always 72 units/inch.  For
raster image output, the resolution can be specified when the
:py:attr:`~jvplot.plot.Plot` object is created, one device coordinate
unit always corresponds to one pixel.

Data Coordinates
----------------


Automatic Axis Tick Placement
=============================

Problem Statement
-----------------

Axis tick placement should take the following information into
account:

* Non-empty data ranges :math:`[x_1, x_2]` and :math:`[y_1, y_2]` in
  data units,

* the axes area dimensions, given by the width :math:`w` and height
  :math:`h` in device coordinate units, and

* optionally, an aspect ratio :math:`\alpha`.

The aim of automatix tick placement is to determine, for each axis,
good values for the following parameters:

* The range :math:`[x_0, x_3]` and :math:`[y_0, y_3]` of data
  coordinate units covered by by the axes.

* The spacing :math:`d_x` and :math:`d_y` of tick marks in data
  coordinates; ticks will be placed at every visible integer multiple
  of the tick spacing.

Thus, six parameters in total need to be determined.  The solution
must satisfy the following hard constraints:

1. The whole data range must be contained in the axes range, *i.e.*
   :math:`x_0 \leq x_1 < x_2 \leq x_3` and :math:`y_0 \leq y_1 < y_2
   \leq y_3` must be satisfied.

2. If an aspect ratio :math:`\alpha` is given, the condition

   .. math::

       \frac{x_3 - x_0}{w} = \alpha \frac{y_3 - y_0}{h}

   must be satisfied, *i.e.* the scale in horizontal direction must
   equal :math:`\alpha` times the scale in vertical direction.

3. The tick spacings :math:`d_x` and :math:`d_y` must be of the form
   :math:`d = c \cdot 10^k` where :math:`c \in \{ 1.0, 2.0, 2.5, 5.0
   \}` and :math:`k` is an integer.

4. There exist integers :math:`k_x` and :math:`k_y` such that
   :math:`x_0 \leq k_x d_x < (k_x+1) d_x \leq x_3` and :math:`y_0 \leq
   k_y d_y < (k_y+1) d_y \leq y_3`, *i.e.* at least two tick marks are
   visible on each axis.

There are infinitely many solutions which satisfy these constraints.
Good solutions have as many of the following properties as possible:

* If possible, the tick labels (when typeset using the appropriate
  font) don't overlap.

* The spacing of the tick marks, when converted to device coordinates,
  is close to the optimal label spacing given by the
  :code:`axis_tick_opt_spacing` parameter.

* :math:`\lceil x_0/d_x \rceil - x_0/d_x` (x-axis length before the
  first tick mark), :math:`x_3/d_x - \lfloor x_3/d_x \rfloor` (x-axis
  length after the last tick mark), :math:`\lceil y_0/d_y \rceil -
  y_0/d_y` (y-axis length below the first tick mark), and
  :math:`y_3/d_y - \lfloor y_3/d_y \rfloor` (y-axis length above the
  last tick mark) are small.

* The used fraction of the axes area, *i.e.*

  .. math::

      \frac{(x_2 - x_1)(y_2 - y_1)}{(x_3 - x_0)(y_3 - y_0)}

  is large (*i.e.* close to one).

Algorithm
---------

Since finding the optimal solution for the tick placement problem
seems difficult, JvPlot uses an approximate algorithm, described in
the following sections.

Penalty function
................

Quality of the solutions is compared using a penalty function.  The
penalty for the x-axis is composed of four individual components:

.. code::

	/ 0,                            if labels don't overlap, and
   p0 = |
	\ 1 + percentage of overlap     otherwise

   p1 = abs(log(dx / opt_d))

   p2 = (ceil(x0/dx) - x0/dx)**2 + (x3/dx - floor(x3/dx))**2

   p3 = log2((x3-x0) / (x2-x1))

Calculation of the penalty vector is implemented by the following
internal function:

.. autofunction:: axes._axis_penalties

The total penalty for the x-axis is then

.. code::

   p = c0 * p0 + c1 * p1 + c2 * p2 + c3 * p3

The analogous expression for the y-axis give a total penalty for the
y-axis.  Finally, the sum of these axis penalties is used as the
penalty for the pair of axes.


Unspecified Aspect Ratio
........................

If the aspect ratio is not specified, the ticks for both axes can be
found independently.  The algorithm is here specified for the x-axis,
the algorithm for the y-axis is found by making the obvious
replacements.

.. code::

   for "all tick spacings dx in decreasing order, starting with the smallest dx >= x2 - x1":
       a = "largest tick position <= x1"
       for x0 in [a, x1]:
	   b = "smallest tick position >= x2"
	   for x3 in [x2, b]:
	       p = "penalty for (x0, x3, dx)"
	       if p < "penalty of current best solution":
		   store (x0, x3, dx) as the new best solution
       if "solution has not improved two times in a row":
	   break

Specified Aspect Ratio
......................

If an aspect ratio is specified, both axes need to be considered
simultaneously: because the aspect ratio relation

   .. math::
       y_3 - y_0 = \frac{h}{\alpha w} (x_3 - x_0)

must be satisfied, only three of the four values :math:`x_0, x_3, y_0,
y_3` can be chosen indenpendently.
