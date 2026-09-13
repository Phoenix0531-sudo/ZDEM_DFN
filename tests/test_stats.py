"""stats 模块测试：几何推导、分箱、p21 对比、报告写出（MD/CSV）。"""
from zdem_dfn.stats import (
    compute_network_stats,
    write_stats_report,
)

# 已知几何：水平段长 100、45° 段长 100*sqrt(2)、竖直段长 50
FRACTURES = [
    ((0.0, 0.0), (100.0, 0.0)),          # dip 0°, len 100
    ((0.0, 0.0), (100.0, 100.0)),        # dip 45°, len ~141.4
    ((0.0, 0.0), (0.0, 50.0)),           # dip 90°, len 50
]


def test_compute_network_stats_basics():
    s = compute_network_stats(FRACTURES, 0.0, 1000.0, 0.0, 1000.0)
    assert s["count"] == 3
    assert abs(s["total_length"] - (100.0 + 100.0 * 2 ** 0.5 + 50.0)) < 1e-9
    assert abs(s["min_length"] - 50.0) < 1e-9
    assert abs(s["max_length"] - 100.0 * 2 ** 0.5) < 1e-9
    # p21 实际 = 总迹长 / 面积
    assert abs(s["p21_actual"] - s["total_length"] / 1_000_000.0) < 1e-15


def test_dip_bins():
    s = compute_network_stats(FRACTURES, 0.0, 1000.0, 0.0, 1000.0)
    assert len(s["dip_bins"]) == 18  # 180 / 10
    assert sum(s["dip_bins"]) == 3
    assert s["dip_bins"][0] == 1     # 0-10°
    assert s["dip_bins"][4] == 1     # 40-50°
    assert s["dip_bins"][9] == 1     # 90-100°


def test_dip_wraps_negative_to_180():
    """-45° 方向（dx>0, dy<0）应折到 135°。"""
    s = compute_network_stats([((0.0, 0.0), (100.0, -100.0))],
                              0.0, 1000.0, 0.0, 1000.0)
    assert s["dip_bins"][13] == 1  # 130-140°


def test_empty_fractures():
    s = compute_network_stats([], 0.0, 1000.0, 0.0, 1000.0)
    assert s["count"] == 0
    assert s["total_length"] == 0.0
    assert s["p21_actual"] == 0.0
    assert sum(s["dip_bins"]) == 0


def test_p21_target_read_at_call_time(monkeypatch):
    from zdem_dfn import config
    monkeypatch.setattr(config, "FRACTURE_SETS",
                        [{"name": "T", "p21": 0.5, "length_mult": 1.0,
                          "length_std_ratio": 0.1, "dip_mean": 0.0, "dip_std": 1.0}])
    s = compute_network_stats([], 0.0, 1000.0, 0.0, 1000.0)
    assert s["p21_target"] == 0.5


def test_write_markdown_report(tmp_path):
    s = compute_network_stats(FRACTURES, 0.0, 1000.0, 0.0, 1000.0)
    p = tmp_path / "report.md"
    write_stats_report(s, str(p), tag_counts={"DFN_Matrix": 42})
    text = p.read_text(encoding="utf-8")
    assert "p21" in text and "方向角分布" in text and "迹长分布" in text
    assert "DFN_Matrix" in text and "42" in text


def test_write_csv_report(tmp_path):
    s = compute_network_stats(FRACTURES, 0.0, 1000.0, 0.0, 1000.0)
    p = tmp_path / "report.csv"
    write_stats_report(s, str(p))
    text = p.read_text(encoding="utf-8")
    assert "p21_actual" in text and "dip_bin_deg" in text
