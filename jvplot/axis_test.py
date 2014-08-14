import nose.tools
import numpy as np
import os.path
import shutil
import tempfile
import unittest

from . import axis
from . import plot

def test_scale():
    assert axis._scale(0) == 1
    nose.tools.assert_almost_equals(axis._scale(1), 2)
    nose.tools.assert_almost_equals(axis._scale(2), 2.5)
    nose.tools.assert_almost_equals(axis._scale(3), 5)
    nose.tools.assert_almost_equals(axis._scale(4), 10)

def test_next_scale():
    for x in np.linspace(0.1, 100, 1001):
        k = axis._next_scale(x)
        y = axis._scale(k)
        assert y > x, "%f (tick %d) > %f failed" % (y, k, x)
        z = axis._scale(k-1)
        assert z <= x, "%f (tick %d) <= %f failed" % (z, k-1, x)

class AxesPenaltyTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        fname = os.path.join(self.tempdir, "test.pdf")
        self.plot = plot.Plot(fname, 720, 360)
        self.plot.set_limits((0, 1), (0, 3))

    def tearDown(self):
        self.plot.close()
        shutil.rmtree(self.tempdir)

    def test_p0(self):
        label = "hello"
        labels = [label, label]

        # horizontal axis
        h_ext = self.plot.ctx.text_extents(label)
        width = h_ext[4] / self.plot.scale[0]

        ticks = [0, width]
        p = axis._penalties(self.plot.width, (0,1), (0,1), ticks, labels, True,
                            self.plot.ctx, 0.0, 1.0)
        nose.tools.assert_almost_equals(p[0], 0)

        ticks = [0, 2*width]
        p = axis._penalties(self.plot.width, (0,1), (0,1), ticks, labels, True,
                            self.plot.ctx, 0.0, 1.0)
        nose.tools.assert_almost_equals(p[0], 0)

        ticks = [0, .5*width]
        p = axis._penalties(self.plot.width, (0,1), (0,1), ticks, labels, True,
                            self.plot.ctx, 0.0, 1.0)
        nose.tools.assert_almost_equals(p[0], 1 + .5)

        ticks = [0, width]
        p = axis._penalties(self.plot.width, (0,1), (0,1), ticks, labels, True,
                            self.plot.ctx, h_ext[4], 1.0)
        nose.tools.assert_almost_equals(p[0], 1 + .5)

        # vertical axis
        v_ext = self.plot.ctx.font_extents()
        height = v_ext[2] / self.plot.scale[1]

        ticks = [0, height]
        p = axis._penalties(self.plot.height, (0,3), (0,3), ticks, labels, False,
                            self.plot.ctx, 0.0, 1.0)
        nose.tools.assert_almost_equals(p[0], 0)

        ticks = [0, 2*height]
        p = axis._penalties(self.plot.height, (0,3), (0,3), ticks, labels, False,
                            self.plot.ctx, 0.0, 1.0)
        nose.tools.assert_almost_equals(p[0], 0)

        ticks = [0, .5*height]
        p = axis._penalties(self.plot.height, (0,3), (0,3), ticks, labels, False,
                            self.plot.ctx, 0.0, 1.0)
        nose.tools.assert_almost_equals(p[0], 1 + .5)

        ticks = [0, height]
        p = axis._penalties(self.plot.height, (0,3), (0,3), ticks, labels, False,
                            self.plot.ctx, v_ext[2], 1.0)
        nose.tools.assert_almost_equals(p[0], 1 + .5)

        # no labels
        p = axis._penalties(self.plot.height, (0,3), (0,3), ticks, None, False,
                            self.plot.ctx, v_ext[2], 1.0)
        nose.tools.assert_almost_equals(p[0], 0)

    def test_p1(self):
        ticks = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
        p = axis._penalties(10, (0,1), (0,1), ticks, None, True,
                            None, 1, 2.0)
        nose.tools.assert_almost_equals(p[1], 0)

    # TODO(voss): implement unit tests for p2

    def test_p3(self):
        p = axis._penalties(self.plot.height, (0, 1), (0, 1), [], [], True,
                            None, 1, 1)
        nose.tools.assert_almost_equals(p[3], 0)
        p = axis._penalties(self.plot.height, (0, 1), (0, 2), [], [], True,
                            None, 1, 1)
        nose.tools.assert_almost_equals(p[3], 1.0)

def test_axes_without_aspect():
    with tempfile.TemporaryDirectory() as tmpdir:
        limits = [ (0,1), (0,0), (1, 999), (-1, 1001) ]
        for x_lim in limits:
            for y_lim in limits:
                fname = os.path.join(tmpdir, "test.pdf")
                fig = plot.Plot(fname, 5, 5)
                fig.draw_axes(x_lim, y_lim)
                plot_x_lim = fig.axes.x_lim
                plot_y_lim = fig.axes.y_lim
                print("x_lim", x_lim, plot_x_lim, "y_lim", y_lim, plot_y_lim)
                assert plot_x_lim[0] <= x_lim[0] <= x_lim[1] <= plot_x_lim[1]
                assert plot_y_lim[0] <= y_lim[0] <= y_lim[1] <= plot_y_lim[1]
                fig.close()

def test_axes_with_aspect():
    with tempfile.TemporaryDirectory() as tmpdir:
        limits = [ (0,1), (0,0), (1, 999), (-1, 1001) ]
        for x_lim in limits:
            for y_lim in limits:
                for aspect in [ 1, .5, 2 ]:
                    fname = os.path.join(tmpdir, "test.pdf")
                    fig = plot.Plot(fname, 5, 5)
                    fig.draw_axes(x_lim, y_lim, aspect=1)
                    plot_x_lim = fig.axes.x_lim
                    plot_y_lim = fig.axes.y_lim
                    print("x_lim", x_lim, plot_x_lim, "y_lim", y_lim, plot_y_lim)
                    assert plot_x_lim[0] <= x_lim[0] <= x_lim[1] <= plot_x_lim[1]
                    assert plot_y_lim[0] <= y_lim[0] <= y_lim[1] <= plot_y_lim[1]
                    nose.tools.assert_almost_equals(
                        (plot_x_lim[1] - plot_x_lim[0]) / (plot_y_lim[1] - plot_y_lim[0]),
                        fig.axes.width / fig.axes.height)
                    fig.close()
