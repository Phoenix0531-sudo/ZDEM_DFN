"""陌生用户入口的端到端测试：真实 subprocess + --input/--output。"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write_case(folder: Path, count: int = 24) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    rows = [
        "# Synthetic demo data (not laboratory measurements)",
        "# Columns: x y r; units follow the upstream ZDEM convention.",
    ]
    for i in range(count):
        x = 2200.0 + (i % 8) * 450.0
        y = 3300.0 + (i // 8) * 2600.0
        rows.append(f"{x:.12e}  {y:.12e}  {120.0:.12e}")
    source = folder / "ini_xyr.dat"
    source.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return source


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.update({"MPLBACKEND": "Agg", "PYTHONUTF8": "1"})
    return subprocess.run(
        [sys.executable, "-m", "zdem_dfn", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        timeout=120,
    )


def test_cli_help_is_actionable():
    result = _run("--help")
    assert result.returncode == 0
    assert "--input" in result.stdout
    assert "--output" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--in-place" in result.stdout
    assert "examples/demo_case" in result.stdout


def test_input_output_mode_creates_complete_case(tmp_path):
    source = _write_case(tmp_path / "case")
    before = source.read_bytes()
    output = tmp_path / "outputs" / "case"
    result = _run("--input", str(source.parent), "--output", str(output), "--seed", "42")

    assert result.returncode == 0, result.stderr
    assert output.joinpath("ini_xyr_dfn.dat").is_file()
    image = output / "dfn_preview.png"
    assert image.is_file() and image.stat().st_size > 0
    from PIL import Image
    with Image.open(image) as rendered:
        rendered.verify()
    assert source.read_bytes() == before
    assert not source.parent.joinpath("ini_xyr_dfn.dat").exists()
    assert "输出文件" in result.stdout


def test_default_mode_preserves_source_bytes(tmp_path):
    source = _write_case(tmp_path / "case")
    before = source.read_bytes()
    output = tmp_path / "out"
    result = _run("--input", str(source.parent), "--output", str(output), "--seed", "7")

    assert result.returncode == 0, result.stderr
    assert source.read_bytes() == before
    assert output.joinpath("ini_xyr_dfn.dat").read_bytes() != before


def test_dry_run_is_zero_write_and_reports_plan(tmp_path):
    source = _write_case(tmp_path / "case")
    before = source.read_bytes()
    output = tmp_path / "planned-output"
    result = _run("--input", str(source.parent), "--output", str(output), "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "dry-run" in result.stdout
    assert not output.exists()
    assert source.read_bytes() == before


def test_missing_input_is_friendly_error(tmp_path):
    output = tmp_path / "out"
    result = _run("--input", str(tmp_path / "missing"), "--output", str(output))

    assert result.returncode != 0
    assert "缺少颗粒文件" in result.stdout
    assert "Traceback" not in result.stdout
    assert not output.exists()


def test_invalid_particle_file_is_friendly_error(tmp_path):
    case = tmp_path / "bad"
    case.mkdir()
    (case / "ini_xyr.dat").write_text("not a particle row\n", encoding="utf-8")
    result = _run("--input", str(case), "--output", str(tmp_path / "out"))

    assert result.returncode != 0
    assert "无有效颗粒行" in result.stdout
    assert "Traceback" not in result.stdout


def test_input_requires_output_directory(tmp_path):
    result = _run("--input", str(tmp_path))
    assert result.returncode == 2
    assert "必须与 --output 一起使用" in result.stderr


def test_input_and_output_flag_conflicts_are_rejected(tmp_path):
    result = _run("--input", str(tmp_path), "--dirs", str(tmp_path))
    assert result.returncode == 2
    assert "不能同时使用" in result.stderr
