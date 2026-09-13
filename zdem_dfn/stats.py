"""网络统计报告：p21 实际 vs 目标、倾向分布、迹长分布。

只做只读统计，不参与网络生成。数据全部由已有几何对象（裂隙线段端点）
推导：迹长 = 两端点欧氏距离；方向角 = atan2(dy, dx) 折到 [0, 180)。
"""
from __future__ import annotations

import csv
import math
import os
from collections.abc import Sequence
from typing import Any

from zdem_dfn import config

# 裂隙线段：((x1, y1), (x2, y2)) —— 与 dfn.generate_dfn_network 返回值一致
Segment = tuple[tuple[float, float], tuple[float, float]]

DIP_BIN_DEG = 10.0
LENGTH_BIN_COUNT = 10


def _segment_length_and_dip(seg: Segment) -> tuple[float, float]:
    """端点对 → (迹长, 方向角[0,180))。"""
    (x1, y1), (x2, y2) = seg
    length = math.hypot(x2 - x1, y2 - y1)
    dip = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180.0
    return length, dip


def compute_dip_bins(dips: Sequence[float],
                      bin_size: float = DIP_BIN_DEG,
                      max_deg: float = 180.0) -> list[int]:
    """方向角直方图分箱。返回长度 round(max_deg/bin_size) 的计数列表。"""
    n_bins = max(1, int(round(max_deg / bin_size)))
    bins = [0] * n_bins
    for dip in dips:
        idx = min(int(dip // bin_size), n_bins - 1)
        bins[idx] += 1
    return bins


def compute_network_stats(fractures: Sequence[Segment],
                          min_x: float, max_x: float,
                          min_y: float, max_y: float) -> dict[str, Any]:
    """统计裂隙网络。

    返回 dict：
    - count / total_length / mean_length / min_length / max_length
    - p21_actual（总迹长/面积）与 p21_target（各 FRACTURE_SETS 之和，运行时读 config）
    - dip_bins：以 10° 分箱的方向角计数（含上界闭合 bin）
    - length_bins：10 个等宽迹长区间的计数
    - window：统计窗口（面积、X/Y 范围）
    """
    area = (max_x - min_x) * (max_y - min_y)

    lengths: list[float] = []
    dips: list[float] = []
    for seg in fractures:
        length, dip = _segment_length_and_dip(seg)
        lengths.append(length)
        dips.append(dip)

    p21_target = 0.0
    for fset in config.FRACTURE_SETS:
        p21_target += float(fset.get("p21", 0.0))

    dip_bins = compute_dip_bins(dips)

    if lengths:
        lo, hi = min(lengths), max(lengths)
        width = (hi - lo) / LENGTH_BIN_COUNT if hi > lo else 1.0
        length_bins = [0] * LENGTH_BIN_COUNT
        for length in lengths:
            idx = min(int((length - lo) / width), LENGTH_BIN_COUNT - 1)
            length_bins[idx] += 1
        length_bin_edges = [lo + i * width for i in range(LENGTH_BIN_COUNT + 1)]
    else:
        length_bins = [0] * LENGTH_BIN_COUNT
        length_bin_edges = [0.0] * (LENGTH_BIN_COUNT + 1)

    total_length = sum(lengths)
    return {
        "count": len(fractures),
        "total_length": total_length,
        "mean_length": total_length / len(fractures) if fractures else 0.0,
        "min_length": min(lengths) if lengths else 0.0,
        "max_length": max(lengths) if lengths else 0.0,
        "p21_actual": total_length / area if area > 0 else 0.0,
        "p21_target": p21_target,
        "window_area": area,
        "window": (min_x, max_x, min_y, max_y),
        "dip_bin_size": DIP_BIN_DEG,
        "dip_bins": dip_bins,
        "length_bin_edges": length_bin_edges,
        "length_bins": length_bins,
    }


def _fmt(v: float) -> str:
    return f"{v:.4f}"


def write_stats_report(stats: dict[str, Any], path: str,
                       tag_counts: dict[str, int] | None = None) -> None:
    """写统计报告。``.csv`` 后缀 → CSV；其余 → Markdown。

    tag_counts：可选的颗粒标签计数（如 {"DFN_Matrix": 1503, ...}）附在报告尾部。
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        _write_csv(stats, path)
        return
    _write_markdown(stats, path, tag_counts)


def _write_csv(stats: dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        for key in ("count", "total_length", "mean_length",
                    "min_length", "max_length", "p21_actual",
                    "p21_target", "window_area"):
            w.writerow([key, _fmt(float(stats[key]))])
        w.writerow([])
        w.writerow(["dip_bin_deg", "count"])
        for i, c in enumerate(stats["dip_bins"]):
            w.writerow([f"{i * stats['dip_bin_size']:.0f}-"
                        f"{(i + 1) * stats['dip_bin_size']:.0f}", c])
        w.writerow([])
        edges = stats["length_bin_edges"]
        w.writerow(["length_bin", "count"])
        for i, c in enumerate(stats["length_bins"]):
            w.writerow([f"{edges[i]:.2f}-{edges[i + 1]:.2f}", c])


def _write_markdown(stats: dict[str, Any], path: str,
                    tag_counts: dict[str, int] | None) -> None:
    window = stats["window"]
    lines: list[str] = []
    lines.append("# DFN 网络统计报告")
    lines.append("")
    lines.append(f"- 统计窗口：X {window[0]:.1f} ~ {window[1]:.1f}，"
                 f"Y {window[2]:.1f} ~ {window[3]:.1f}（面积 {stats['window_area']:.1f}）")
    lines.append(f"- 裂隙条数：{stats['count']}")
    lines.append(f"- 总迹长：{stats['total_length']:.2f}")
    lines.append(f"- 迹长均值 / 最小 / 最大：{stats['mean_length']:.2f} / "
                 f"{stats['min_length']:.2f} / {stats['max_length']:.2f}")
    if stats["p21_target"] > 0:
        rate = stats["p21_actual"] / stats["p21_target"] * 100
        lines.append(f"- p21（实际 / 目标）：{stats['p21_actual']:.6f} / "
                     f"{stats['p21_target']:.6f}（达成率 {rate:.1f}%）")
    else:
        lines.append(f"- p21（实际 / 目标）：{stats['p21_actual']:.6f} / "
                     f"{stats['p21_target']:.6f}")
    lines.append("")
    lines.append("## 方向角分布（每 10°）")
    lines.append("")
    lines.append("| 区间(°) | 条数 |")
    lines.append("|---|---|")
    for i, c in enumerate(stats["dip_bins"]):
        lo = i * stats["dip_bin_size"]
        hi = (i + 1) * stats["dip_bin_size"]
        lines.append(f"| {lo:.0f}–{hi:.0f} | {c} |")
    lines.append("")
    lines.append("## 迹长分布（10 等分箱）")
    lines.append("")
    lines.append("| 区间 | 条数 |")
    lines.append("|---|---|")
    edges = stats["length_bin_edges"]
    for i, c in enumerate(stats["length_bins"]):
        lines.append(f"| {edges[i]:.2f}–{edges[i + 1]:.2f} | {c} |")
    if tag_counts:
        lines.append("")
        lines.append("## 颗粒标签计数")
        lines.append("")
        lines.append("| 标签 | 颗粒数 |")
        lines.append("|---|---|")
        for tag, n in sorted(tag_counts.items()):
            lines.append(f"| {tag} | {n} |")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
