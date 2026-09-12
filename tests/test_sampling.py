"""sampling 模块单测：相交语义（<=、逐裂隙计数）、节点惩罚、概率分带。"""
import copy

from zdem_dfn import config
from zdem_dfn.sampling import (
    apply_fracture_tagging,
    check_particles_overlap,
    process_single_folder_lines,
    random_tag_by_probability,
)


def _p(pid, x, y, r):
    return {"type": "particle", "raw": "r", "p_id": pid, "x": x, "y": y, "r": r,
            "intersect_count": 0, "tag": None}


H_FRAC = [((0.0, 510.0), (1000.0, 510.0))]  # 水平裂隙 y=510


def test_boundary_touch_counts_as_intersect():
    """dist == r 恰好相切时必须计入（旧引擎 <= 语义）。"""
    lines = [_p(1, 500.0, 500.0, 10.0)]  # 距裂隙恰好 10
    stats = apply_fracture_tagging(lines, H_FRAC, grid_cell_size=100.0, max_r=10.0)
    assert lines[0]["intersect_count"] == 1
    assert stats["DFN_Matrix"] == 1


def test_per_fracture_count_accumulates():
    """两条裂隙都命中 → intersect_count=2（不是首中即停）。"""
    two_fracs = H_FRAC + [((0.0, 490.0), (1000.0, 490.0))]
    lines = [_p(1, 500.0, 500.0, 10.0)]
    apply_fracture_tagging(lines, two_fracs, grid_cell_size=100.0, max_r=10.0)
    assert lines[0]["intersect_count"] == 2


def test_node_penalty_double_hit(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_NODE_PENALTY", True)
    monkeypatch.setattr(config, "ENABLE_HETEROGENEOUS", True)
    monkeypatch.setattr(config, "PROB_ASPERITY", 0.15)
    monkeypatch.setattr(config, "PROB_MATRIX", 0.60)
    two_fracs = H_FRAC + [((0.0, 490.0), (1000.0, 490.0))]
    lines = [_p(1, 500.0, 500.0, 10.0), _p(2, 500.0, 700.0, 10.0)]
    stats = apply_fracture_tagging(lines, two_fracs, grid_cell_size=100.0, max_r=10.0)
    assert lines[0]["tag"] == "DFN_Node"  # 双命中
    assert lines[1]["tag"] is None       # 未命中
    assert stats["DFN_Node"] == 1


def test_heterogeneous_probability_bands(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_HETEROGENEOUS", True)
    monkeypatch.setattr(config, "ENABLE_NODE_PENALTY", False)
    monkeypatch.setattr(config, "PROB_ASPERITY", 1.0)   # 全部 Asperity
    lines = [_p(1, 500.0, 500.0, 10.0)]
    stats = apply_fracture_tagging(lines, H_FRAC, grid_cell_size=100.0, max_r=10.0)
    assert lines[0]["tag"] == "DFN_Asperity"

    monkeypatch.setattr(config, "PROB_ASPERITY", 0.0)
    monkeypatch.setattr(config, "PROB_MATRIX", 1.0)     # 全部 Matrix
    lines = [_p(1, 500.0, 500.0, 10.0)]
    stats = apply_fracture_tagging(lines, H_FRAC, grid_cell_size=100.0, max_r=10.0)
    assert lines[0]["tag"] == "DFN_Matrix"

    monkeypatch.setattr(config, "PROB_MATRIX", 0.0)     # 剩余全落 Gouge
    lines = [_p(1, 500.0, 500.0, 10.0)]
    stats = apply_fracture_tagging(lines, H_FRAC, grid_cell_size=100.0, max_r=10.0)
    assert lines[0]["tag"] == "DFN_Gouge"
    assert stats["DFN_Gouge"] == 1


def test_grid_matches_bruteforce(monkeypatch):
    """网格哈希结果与暴力遍历（process_single_folder_lines）完全一致。"""
    monkeypatch.setattr(config, "ENABLE_HETEROGENEOUS", False)
    monkeypatch.setattr(config, "ENABLE_NODE_PENALTY", False)
    import random
    rng = random.Random(7)
    fracs = []
    for _ in range(30):
        x, y = rng.uniform(0, 1000), rng.uniform(0, 1000)
        fracs.append(((x, y), (rng.uniform(0, 1000), rng.uniform(0, 1000))))
    base = [_p(i, rng.uniform(0, 1000), rng.uniform(0, 1000), rng.uniform(5, 30))
            for i in range(200)]

    a = copy.deepcopy(base)
    apply_fracture_tagging(a, fracs, grid_cell_size=80.0, max_r=30.0)
    b = copy.deepcopy(base)
    process_single_folder_lines(fracs, b)

    for pa, pb in zip(a, b, strict=True):
        assert pa["intersect_count"] == pb["intersect_count"]
        assert pa["tag"] == pb["tag"]


def test_check_particles_overlap():
    assert check_particles_overlap(0, 0, 10, 15, 0, 10) is True
    assert check_particles_overlap(0, 0, 10, 25, 0, 10) is False
    assert check_particles_overlap(0, 0, 10, 21, 0, 10, min_gap=1.0) is False  # 21 == 10+10+1，不含等于
    assert check_particles_overlap(0, 0, 10, 20.5, 0, 10, min_gap=1.0) is True


def test_random_tag_by_probability_default(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_HETEROGENEOUS", False)
    assert random_tag_by_probability() == "DFN_Matrix"
