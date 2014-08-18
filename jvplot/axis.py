import math
import numpy as np

_q = 10**0.25 / 2

def _scale_length(k):
    """Get the scale length k.

    Scale lengths are indexed by integers k, and are ..., 0.1, 0.2,
    0.25, 0.5, 1.0, 2.0, 2.5, 5.0, 10.0, ..., where k=0 corresponds to
    the scale length 1.0.  Larger values of k correspond to larger
    scale lengths.

    """
    c = [1.0, 2.0, 2.5, 5.0][k%4]
    return c * 10**(k//4)

def _smallest_scale_larger_than(x):
    """Get the smallest scale with scale length >=x.  This corresponds to
    rounding up to the nearest scale length.

    """
    k = math.floor(math.log10(_q * x) * 4) + 1
    if _scale_length(k) <= x:
        k += 1
    return k

def _ticks(a, b, spacing):
    start = math.ceil(a / spacing)
    stop = math.floor(b / spacing)
    return [k * spacing for k in range(start, stop+1)]

def _try_single(lim):
    """Generate a selection of plausible axis tick placements.  This
    generator yields 2-tuples containing the suggested axis limits and
    tick label positions.

    """
    k0 = _smallest_scale_larger_than(lim[1] - lim[0])
    for k in range(k0 - 3, k0 + 1):
        spacing = _scale_length(k)
        i0 = math.floor(lim[0] / spacing)
        i1 = math.ceil(lim[1] / spacing)
        ticks = [k * spacing for k in range(i0, i1+1)]
        yield (i0*spacing, i1*spacing), ticks
        if len(ticks) > 2:
            yield (lim[0], i1*spacing), ticks[1:]
            yield (i0*spacing, lim[1]), ticks[:-1]
        if len(ticks) > 3:
            yield (lim[0], lim[1]), ticks[1:-1]

def _try_second(lim, length):
    assert lim[1] - lim[0] <= length
    mid = (lim[0] + lim[1]) / 2
    a = mid - length / 2
    b = mid + length / 2

    k0 = _smallest_scale_larger_than(lim[1] - lim[0])
    for k in range(k0 - 6, k0 + 1):
        spacing = _scale_length(k)

        candidates = []
        candidates.append((a, b))

        ak = round(mid / spacing) * spacing - length / 2
        bk = round(mid / spacing) * spacing + length / 2
        candidates.append((ak, bk))

        ak = (math.floor(mid / spacing) + .5) * spacing - length / 2
        bk = (math.floor(mid / spacing) + .5) * spacing + length / 2
        candidates.append((ak, bk))

        ak = math.floor(a / spacing) * spacing
        bk = ak + length
        candidates.append((ak, bk))

        bk = math.ceil(b / spacing) * spacing
        ak = bk - length
        candidates.append((ak, bk))

    for a, b in candidates:
        if a > lim[0] or b < lim[1]:
            continue
        i0 = math.ceil(a / spacing)
        i1 = math.floor(b / spacing)
        ticks = [k * spacing for k in range(i0, i1+1)]
        yield (a, b), ticks

def _try_pairs(x_data_lim, y_data_lim, q):
    if x_data_lim[1] - x_data_lim[0] >= (y_data_lim[1] - y_data_lim[0]) * q:
        for x_axis_lim, x_ticks in _try_single(x_data_lim):
            length = (x_axis_lim[1] - x_axis_lim[0]) / q
            for y_axis_lim, y_ticks in _try_second(y_data_lim, length):
                yield x_axis_lim, x_ticks, y_axis_lim, y_ticks
    else:
        for y_axis_lim, y_ticks in _try_single(y_data_lim):
            length = (y_axis_lim[1] - y_axis_lim[0]) * q
            for x_axis_lim, x_ticks in _try_second(x_data_lim, length):
                yield x_axis_lim, x_ticks, y_axis_lim, y_ticks

def _penalties(length, data_lim, axis_lim, ticks, labels, is_parallel,
               font_ctx, min_label_sep, best_tick_dist):
    """Compute the 4 penalty values for a given axis tick configuration.

    :Arguments:

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
