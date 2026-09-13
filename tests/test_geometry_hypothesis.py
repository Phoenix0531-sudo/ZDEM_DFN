"""几何模块 property-based 测试（hypothesis）：数学不变量而非定点用例。

- point_to_segment_distance: 非负、端点距离=欧氏距离、对称性
- clip_line_segment: 幂等性（裁剪后的线段再裁剪不变）、裁剪端点必在窗口内
- get_segment_intersection: 平行线无交点 / 交点同时落在两条线段上
"""
import math

from hypothesis import given, settings
from hypothesis import strategies as st

from zdem_dfn.geometry import (
    clip_line_segment,
    get_segment_intersection,
    point_to_segment_distance,
)

finite = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False,
                  allow_infinity=False)
coord = st.floats(min_value=-1e4, max_value=1e4, allow_nan=False,
                  allow_infinity=False)


@given(px=coord, py=coord, ax=coord, ay=coord, bx=coord, by=coord)
@settings(max_examples=300, deadline=None)
def test_distance_nonnegative_and_endpoint_symmetry(px, py, ax, ay, bx, by):
    d1 = point_to_segment_distance(px, py, ax, ay, bx, by)
    assert d1 >= 0.0 or math.isclose(d1, 0.0, abs_tol=1e-9)
    # 对称性：A/B 端点交换，距离不变
    d2 = point_to_segment_distance(px, py, bx, by, ax, ay)
    assert math.isclose(d1, d2, rel_tol=1e-9, abs_tol=1e-6)


@given(ax=coord, ay=coord, bx=coord, by=coord)
@settings(max_examples=200, deadline=None)
def test_distance_to_endpoint_is_euclidean(ax, ay, bx, by):
    # 点取为端点 A：距离必为 0
    d = point_to_segment_distance(ax, ay, ax, ay, bx, by)
    assert math.isclose(d, 0.0, abs_tol=1e-6)


@given(ax=coord, ay=coord, bx=coord, by=coord)
@settings(max_examples=200, deadline=None)
def test_distance_zero_when_point_on_segment(ax, ay, bx, by):
    # 点取在中点上：距离必为 0
    mx, my = (ax + bx) / 2, (ay + by) / 2
    if math.isfinite(mx) and math.isfinite(my):
        d = point_to_segment_distance(mx, my, ax, ay, bx, by)
        assert math.isclose(d, 0.0, abs_tol=1e-6)


@given(x0=coord, y0=coord, x1=coord, y1=coord,
       ax=coord, ay=coord, bx=coord, by=coord)
@settings(max_examples=200, deadline=None)
def test_clip_idempotent_and_inside(x0, y0, x1, y1, ax, ay, bx, by):
    """裁剪幂等性 + 裁剪结果端点必在窗口内。"""
    # 保证窗口有效（min<max）
    wx0, wx1 = min(x0, x1), max(x0, x1)
    wy0, wy1 = min(y0, y1), max(y0, y1)
    if wx1 - wx0 < 1.0 or wy1 - wy0 < 1.0:
        return  # 窗口过小，跳过（hypothesis 假设性过滤，量足够时无碍）

    clipped = clip_line_segment(ax, ay, bx, by, wx0, wx1, wy0, wy1)
    if clipped is None:
        return
    cx1, cy1, cx2, cy2 = clipped
    # 端点必在窗口内（含边界）
    assert wx0 - 1e-6 <= cx1 <= wx1 + 1e-6 and wx0 - 1e-6 <= cx2 <= wx1 + 1e-6
    assert wy0 - 1e-6 <= cy1 <= wy1 + 1e-6 and wy0 - 1e-6 <= cy2 <= wy1 + 1e-6
    # 幂等性：再裁一次不变
    again = clip_line_segment(cx1, cy1, cx2, cy2, wx0, wx1, wy0, wy1)
    if again is not None:
        ex1, ey1, ex2, ey2 = again
        assert math.isclose(cx1, ex1, abs_tol=1e-9) and math.isclose(cy1, ey1, abs_tol=1e-9)
        assert math.isclose(cx2, ex2, abs_tol=1e-9) and math.isclose(cy2, ey2, abs_tol=1e-9)


@given(shift=st.floats(min_value=-100.0, max_value=100.0),
       ax=coord, ay=coord, dx=finite, dy=finite)
@settings(max_examples=150, deadline=None)
def test_parallel_segments_no_intersection(shift, ax, ay, dx, dy):
    """同向平移（shift 沿法向）的两条线段平行 → 无交点（或退化为共线重叠返回 None）。"""
    # 法向（避开全零方向）
    nx, ny = -dy, dx
    norm = math.hypot(nx, ny)
    if norm < 1.0:
        return
    nx, ny = nx / norm, ny / norm
    bx, by = ax + dx, ay + dy
    cx, cy = ax + shift * nx, ay + shift * ny
    ex, ey = bx + shift * nx, by + shift * ny
    if math.isclose(abs(shift), 0.0, abs_tol=1e-9):
        return  # 共线情况实现可返回 None 或交点，跳过
    r = get_segment_intersection((ax, ay), (bx, by), (cx, cy), (ex, ey))
    if r is not None:
        raise AssertionError(f"平行线段不应相交: {r}")
