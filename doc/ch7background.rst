Background Information
======================

This chapter contains information about designing plots which
influenced the design of hte JvPlot package, but which is not directly
required to use the package.


Automatic Axis Tick Placement
-----------------------------

Axis tick placement should take the following information into
account:

* Non-empty data ranges :math:`[x_1, x_2]` and :math:`[y_1, y_2]` in
  data units,

* the axes area dimensions, given by the width :math:`w` and height
  :math:`h` in device coordinates, and

* optionally, an aspect ratio :math:`\alpha`.

The aim of automatix tick placement is to determine, for each axis,
good values for the following parameters:

* The range :math:`[x_0, x_3]` of data coordinates covered by by the
  axis.

* The spacing :math:`d` of tick marks in data coordinates; ticks will
  be placed at every visible integer multiple of :math:`d`

Thus, three parameters per axis (*i.e.* six parameters in total) need
to be found.  The solution must satisfy the following hard
constraints:

1. The whole data range must be contained in the axes range, *i.e.*
   :math:`x_0 \leq x_1 < x_2 \leq x_3` and :math:`y_0 \leq y_1 < y_2
   \leq y_3` must be satisfied.

2. The tick spacings :math:`d_x` and :math:`d_y` must be of the form
   :math:`d = c \cdot 10^k` where :math:`c \in \{ 1.0, 2.0, 2.5, 5.0
   \}` and :math:`k` is an integer.

3. If an aspect ratio :math:`\alpha` is given, the condition

   .. math::

       \frac{x_3 - x_0}{w} = \alpha \frac{y_3 - y_0}{h}

   must be satisfied, *i.e.* the scale in horizontal direction must
   equal :math:`\alpha` times the scale in vertical direction.

4. There are integers :math:`k_x` and :math:`k_y` such that :math:`x_0
   \leq k_x d_x < (k_x+1) d_x \leq x_3` and :math:`y_0 \leq k_y d_y <
   (k_y+1) d_y \leq y_3`, *i.e.* at least two tick marks are visible
   on each axis.

There are infinitely many solutions which satisfy these constraints.
Good solutions have as many of the following properties as possible:

* The tick labels (when typeset using the appropriate font) don't
  overlap.

* :math:`\lceil x_0/d_x \rceil - x_0/d_x` (x-axis length before the
  first tick mark), :math:`x_3/d_x - \lfloor x_3/d_x \rfloor` (x-axis
  length after the last tick mark), :math:`\lceil y_0/d_y \rceil -
  y_0/d_y` (y-axis length below the first tick mark), and
  :math:`y_3/d_y - \lfloor y_3/d_y \rfloor` (y-axis length above the
  last tick mark) are small.

* The amount of wasted axes area, *i.e.*

  .. math::

      1 - \frac{(x_2 - x_1)(y_2 - y_1)}{(x_3 - x_0)(y_3 - y_0)}

  is small.
