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

def _axis_penalties(data_lim, plot_lim, ticks, labels, aligned_labels,
                    font_ctx, min_label_sep, opt_tick_dist):
    """
    Compute the 4 penalty values for a given tick configuration.

    Arguments:

    data_lim
        The data range to display, in data coordinates.
    plot_lim
        The axis range, in data coordinates.  This must contain `data_lim`.
    ticks
    labels
    aligned_labels
    font_ctx
    min_label_sep
    opt_tick_dist
    """
    p0 = 0.0
    if len(labels) > 1:
        if aligned_labels:
            exts = [font_ctx.text_extents(lab) for lab in labels]
            for i in range(1, len(labels)):
                length = .5*(exts[i-1][4] + exts[i][4]) + min_label_sep
                space = tick[i] - tick[i-1]
                overlap = length - space
                if overlap > 0:
                    p0 += overlap / length
        else:
            font_extents = font_ctx.font_extents()
            for i in range(1, len(labels)):
                length = font_extents[2] + min_label_sep
                space = tick[i] - tick[i-1]
                overlap = length - space
                if overlap > 0:
                    p0 += overlap / length

    p1 = 0.0
    if len(ticks) > 1:
        mean_dist = np.mean(np.array(ticks[1:]) - np.array(ticks[:-1]))
        p1 = abs(math.log(mean_dist / opt_tick_dist))

    p2 = 0.0
    if len(ticks) > 1:
        q_left = plot_lim[0] / (ticks[1] - ticks[0])
        p2 += (math.ceil(q_left) - q_left)**2
        q_right = plot_lim[1] / (ticks[-1] - ticks[-2])
        p2 += (q_right - math.floor(q_right))**2

    p3 = math.log2((plot_lim[1] - plot_lim[0]) / (data_lim[1] - data_lim[0]))

    return [p0, p1, p2, p3]
