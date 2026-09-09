"""io 模块单测：ini_xyr.dat 解析、基准统计、带标签就地输出。"""
import random

from zdem_dfn.io import (
    avg_diameter_of,
    compute_reference_stats,
    output_tagged_coordinates,
    parse_particle_file,
)


def _write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def test_parse_headers_empty_and_particles(tmp_path):
    f = _write(tmp_path / "ini_xyr.dat",
               "# header line\n"
               "\n"
               "1.0e3  2.0e3  5.0e1\n"
               "3.5e3 4.6e3 7.0e1\tDFN_Matrix\n")
    lines = parse_particle_file(str(f))
    types = [item["type"] for item in lines]
    assert types == ["header", "empty", "particle", "particle"]

    p1, p2 = lines[2], lines[3]
    assert (p1["x"], p1["y"], p1["r"]) == (1000.0, 2000.0, 50.0)
    # 历史标签尾巴被清洗：只保留 x y r，恢复科学计数法
    assert (p2["x"], p2["y"], p2["r"]) == (3500.0, 4600.0, 70.0)
    assert p2["raw"] == "3.500000000000e+03  4.600000000000e+03  7.000000000000e+01"
    assert p1["tag"] is None and p2["tag"] is None
    assert p2["p_id"] == 2


def test_parse_short_garbage_rows_are_headers(tmp_path):
    f = _write(tmp_path / "ini_xyr.dat", "only two words\nx y z\n")
    lines = parse_particle_file(str(f))
    assert all(item["type"] == "header" for item in lines)


def test_compute_reference_stats_full_and_empty(tmp_path):
    f = _write(tmp_path / "ini_xyr.dat",
               "0.0e0 0.0e0 1.0e1\n"
               "1.0e3 2.0e3 3.0e1\n")
    stats = compute_reference_stats(str(f))
    assert stats["min_x"] == 0.0 and stats["max_x"] == 1000.0
    assert stats["min_y"] == 0.0 and stats["max_y"] == 2000.0
    assert stats["max_r"] == 30.0
    assert stats["avg_diameter"] == (2 * 10 + 2 * 30) / 2
    assert stats["count"] == 2

    empty = _write(tmp_path / "empty.dat", "# nothing\n")
    assert compute_reference_stats(str(empty)) is None


def test_output_tagged_coordinates_roundtrip(tmp_path):
    f = tmp_path / "ini_xyr.dat"
    lines = [
        {"type": "header", "raw": "# header line"},
        {"type": "empty", "raw": ""},
        {"type": "particle", "raw": "1.000000000000e+03  2.000000000000e+03  5.000000000000e+01",
         "p_id": 1, "x": 1000.0, "y": 2000.0, "r": 50.0, "intersect_count": 1, "tag": "DFN_Matrix"},
        {"type": "particle", "raw": "3.000000000000e+03  4.000000000000e+03  6.000000000000e+01",
         "p_id": 2, "x": 3000.0, "y": 4000.0, "r": 60.0, "intersect_count": 0, "tag": None},
    ]
    output_tagged_coordinates(str(f), lines)
    out = f.read_text(encoding="utf-8").splitlines()
    assert out[0] == "# header line"
    assert out[2] == "1.000000000000e+03  2.000000000000e+03  5.000000000000e+01\tDFN_Matrix"
    assert out[3] == "3.000000000000e+03  4.000000000000e+03  6.000000000000e+01"


def test_output_then_reparse_cleans_tags(tmp_path):
    """整文件往返：写带标签 → 重新解析 → 标签被清洗、颗粒数守恒。"""
    f = _write(tmp_path / "ini_xyr.dat",
               "# round trip\n"
               "1.0e3  1.0e3  2.0e1\n"
               "2.0e3  2.0e3  3.0e1\n")
    lines = parse_particle_file(str(f))
    lines[1]["tag"] = "DFN_Node"
    output_tagged_coordinates(str(f), lines)

    reparsed = parse_particle_file(str(f))
    particles = [p for p in reparsed if p["type"] == "particle"]
    assert len(particles) == 2
    assert all(p["tag"] is None for p in particles)
    assert particles[0]["raw"].endswith("2.000000000000e+01")


def test_avg_diameter_of_mixed_rows(tmp_path):
    lines = [
        {"type": "header", "raw": "#"},
        {"type": "particle", "raw": "r", "x": 0, "y": 0, "r": 10.0},
        {"type": "particle", "raw": "r", "x": 0, "y": 0, "r": 30.0},
    ]
    assert avg_diameter_of(lines) == 40.0  # (2*10 + 2*30) / 2
    assert avg_diameter_of([]) == 0.0
