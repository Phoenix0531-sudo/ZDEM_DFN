"""纯几何算法：点到线段距离、Cohen–Sutherland 线段裁剪、线段求交。"""

import math

INSIDE = 0
LEFT = 1
RIGHT = 2
BOTTOM = 4
TOP = 8


def point_to_segment_distance(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    dx: float = x2 - x1
    dy: float = y2 - y1
    L2: float = dx * dx + dy * dy
    if L2 == 0.0:
        return math.hypot(px - x1, py - y1)

    t: float = ((px - x1) * dx + (py - y1) * dy) / L2
    t = max(0.0, min(1.0, t))
    proj_x: float = x1 + t * dx
    proj_y: float = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def _compute_outcode(x: float, y: float, min_x: float, max_x: float, min_y: float, max_y: float) -> int:
    code: int = INSIDE
    if x < min_x:
        code |= LEFT
    elif x > max_x:
        code |= RIGHT
    if y < min_y:
        code |= BOTTOM
    elif y > max_y:
        code |= TOP
    return code


def clip_line_segment(x1: float, y1: float, x2: float, y2: float, min_x: float, max_x: float,
                      min_y: float, max_y: float) -> tuple[float, float, float, float] | None:
    outcode1: int = _compute_outcode(x1, y1, min_x, max_x, min_y, max_y)
    outcode2: int = _compute_outcode(x2, y2, min_x, max_x, min_y, max_y)
    accept: bool = False

    while True:
        if not (outcode1 | outcode2):
            accept = True
            break
        elif outcode1 & outcode2:
            break
        else:
            outcode_out: int = outcode1 if outcode1 else outcode2
            x: float = 0.0
            y: float = 0.0

            if outcode_out & TOP:
                x = x1 + (x2 - x1) * (max_y - y1) / (y2 - y1)
                y = max_y
            elif outcode_out & BOTTOM:
                x = x1 + (x2 - x1) * (min_y - y1) / (y2 - y1)
                y = min_y
            elif outcode_out & RIGHT:
                y = y1 + (y2 - y1) * (max_x - x1) / (x2 - x1)
                x = max_x
            elif outcode_out & LEFT:
                y = y1 + (y2 - y1) * (min_x - x1) / (x2 - x1)
                x = min_x

            if outcode_out == outcode1:
                x1, y1 = x, y
                outcode1 = _compute_outcode(x1, y1, min_x, max_x, min_y, max_y)
            else:
                x2, y2 = x, y
                outcode2 = _compute_outcode(x2, y2, min_x, max_x, min_y, max_y)

    if accept:
        return (x1, y1, x2, y2)
    else:
        return None


def get_segment_intersection(p1: tuple[float, float], p2: tuple[float, float],
                             p3: tuple[float, float], p4: tuple[float, float]) -> tuple[float, float] | None:
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom: float = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-12:
        return None  # 平行或共线

    t: float = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u: float = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
        px: float = x1 + t * (x2 - x1)
        py: float = y1 + t * (y2 - y1)
        return (px, py)
    return None
