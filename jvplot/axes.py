import math
import numpy as np

_q = 10**0.25 / 2

def _axis_tick_distance(k):
    c = [1.0, 2.0, 2.5, 5.0][k%4]
    return c * 10**(k//4)

def _next_axis_tick(x):
    k = math.floor(math.log10(_q * x) * 4) + 1
    if _axis_tick_distance(k) <= x:
        k += 1
    return k

def _axis_penalties(length, data_lim, axis_lim, ticks, labels, is_parallel,
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
