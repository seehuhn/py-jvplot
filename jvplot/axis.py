import math
import numpy as np

_q = 10**0.25 / 2

def _scale(k):
    c = [1.0, 2.0, 2.5, 5.0][k%4]
    return c * 10**(k//4)

def _ticks(a, b, scale):
    start = math.ceil(a / scale)
    stop = math.floor(b / scale) + 1
    return [ k*scale for k in range(start, stop) ]

def _next_scale(x):
    k = math.floor(math.log10(_q * x) * 4) + 1
    if _scale(k) <= x:
        k += 1
    return k

def _try_pairs(x_lim, x_step, y_lim, y_step, q):
    x_scale = _scale(x_step)
    x_mid = .5*(x_lim[0] + x_lim[1])
    x_r = max(x_lim[1] - x_lim[0], (y_lim[1] - y_lim[0]) * q) / 2
    y_scale = _scale(y_step)
    y_mid = .5*(x_lim[0] + x_lim[1])
    y_r = max(y_lim[1] - y_lim[0], (x_lim[1] - x_lim[0]) / q) / 2

    a = np.floor((x_mid - x_r) / x_scale) * x_scale
    for x0 in [a, x_mid - x_r]:
        b = np.ceil((x_mid + x_r) / x_scale) * x_scale
        for x3 in [x_mid + x_r, b]:
            x_ticks = _ticks(x0, x3, x_scale)
            if len(x_ticks) < 2:
                continue
            s = (x3 - x0) / q
            c1 = y_mid - .5*s
            c2 = np.floor(c1 / y_scale) * y_scale
            for y0, y3 in [(c1, c1+s), (c2, c2+s)]:
                y_ticks = _ticks(y0, y3, y_scale)
                if len(y_ticks) < 2:
                    continue
                print(x0, x3, x_ticks, y0, y3, y_ticks)
                yield (x0, x3), x_ticks, (y0, y3), y_ticks

    a = np.floor((y_mid - y_r) / y_scale) * y_scale
    for y0 in [a, y_mid - y_r]:
        b = np.ceil((y_mid + y_r) / y_scale) * y_scale
        for y3 in [y_mid + y_r, b]:
            y_ticks = _ticks(y0, y3, y_scale)
            if len(y_ticks) < 2:
                continue
            s = (y3 - y0) * q
            c1 = x_mid - .5*s
            c2 = np.floor(c1 / x_scale) * x_scale
            for x0, x3 in [(c1, c1+s), (c2, c2+s)]:
                x_ticks = _ticks(x0, x3, x_scale)
                if len(x_ticks) < 2:
                    continue
                print(x0, x3, x_ticks, y0, y3, y_ticks)
                yield (x0, x3), x_ticks, (y0, y3), y_ticks



def _penalties(length, data_lim, axis_lim, ticks, labels, is_parallel,
               font_ctx, min_label_sep, best_tick_dist):
    """Compute the 4 penalty values for a given axis tick configuration.

    Arguments:

    length
        The total axis length in device coordinate units.
    data_lim
        The data range to display, in data coordinates.
    axis_lim
        The axis range, in data coordinates.  This must contain ``data_lim``.
    ticks
        List of tick locations in data coordinates, in increasing order.
    labels
        The labels to put next to the ticks.  This can be either
        ``None`` (for no labels) or a list of strings.  In the latter
        case, ``labels`` and ``ticks`` must have the same length.
    is_parallel (bool)
        Whether the label texts will be typeset parallel to the axis.
    font_ctx
        The Cairo rendering context to use for determining font dimensions.
    min_label_sep
        The minimal allowed distance between labels, in device
        coordinate units.
    best_tick_dist
        The optimal distance between axis ticks, in device coordinate
        units.

    """
    assert labels is None or len(labels) == len(ticks)

    scale = length / (axis_lim[1] - axis_lim[0])

    p0 = 0.0
    if labels is not None and len(labels) > 1:
        if is_parallel:
            exts = [font_ctx.text_extents(lab) for lab in labels]
            for i in range(1, len(labels)):
                dev_length = .5 * (exts[i-1][4] + exts[i][4]) + min_label_sep
                data_length = dev_length / scale
                space = ticks[i] - ticks[i-1]
                overlap = data_length - space
                if overlap > 0:
                    p0 += 1 + overlap / data_length
        else:
            font_extents = font_ctx.font_extents()
            for i in range(1, len(labels)):
                dev_length = font_extents[2] + min_label_sep
                data_length = dev_length / scale
                space = ticks[i] - ticks[i-1]
                overlap = data_length - space
                if overlap > 0:
                    p0 += 1 + overlap / data_length

    p1 = 0.0
    if len(ticks) > 1:
        mean_dist = np.mean(np.array(ticks[1:]) - np.array(ticks[:-1]))
        p1 = abs(math.log(mean_dist * scale / best_tick_dist))

    p2 = 0.0
    if len(ticks) > 1:
        q_left = axis_lim[0] / (ticks[1] - ticks[0])
        p2 += (math.ceil(q_left) - q_left)**2
        q_right = axis_lim[1] / (ticks[-1] - ticks[-2])
        p2 += (q_right - math.floor(q_right))**2

    p3 = math.log2((axis_lim[1] - axis_lim[0]) / (data_lim[1] - data_lim[0]))

    return [p0, p1, p2, p3]
