"""dfn 生成器单测：种子可复现、几何约束、p21 收敛上界。"""
import math
import random

from zdem_dfn.dfn import generate_dfn_network


def _gen(seed=42, area=1000.0 * 1000.0):
    random.seed(seed)
    return generate_dfn_network(area, 0.0, 1000.0, 0.0, 1000.0, avg_diameter=50.0)


def test_same_seed_reproducible_snapshot():
    f1, n1 = _gen(seed=42)
    f2, n2 = _gen(seed=42)
    assert f1 == f2  # 精确逐条相等
    assert n1 == n2


def test_different_seed_differs():
    f1, _ = _gen(seed=42)
    f2, _ = _gen(seed=43)
    assert f1 != f2


def test_fractures_inside_bbox_and_positive_length():
    fractures, _ = _gen()
    assert len(fractures) > 0
    for (x1, y1), (x2, y2) in fractures:
        for x, y in ((x1, y1), (x2, y2)):
            assert 0.0 <= x <= 1000.0
            assert 0.0 <= y <= 1000.0
        assert math.hypot(x2 - x1, y2 - y1) > 0.0


def test_total_length_approximates_p21_area():
    """实测总长应接近 area*p21（裁剪后逐条累加，不应大幅欠采样）。"""
    from zdem_dfn import config
    target = sum(1000.0 * 1000.0 * float(s["p21"]) for s in config.FRACTURE_SETS)

    fractures, _ = _gen()
    total = sum(math.hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in fractures)
    assert total >= target * 0.9  # 裁剪丢段允许 10% 损耗，不允许更少


def test_empty_area_no_fractures():
    """退化工况：p21 与面积乘积为 0 时不生成裂隙。"""
    fractures, n = _gen(seed=7, area=0.0)
    assert n == 0
