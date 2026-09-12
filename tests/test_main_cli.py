"""CLI 与批处理编排测试：退出码、dry-run、端到端管线、种子复现。"""
import random

import pytest

from zdem_dfn import config
from zdem_dfn.main import build_arg_parser, main, run_batch


def _make_specimen(folder, n=40, seed=11):
    rng = random.Random(seed)
    p = folder / "ini_xyr.dat"
    rows = ["# synthetic test specimen", "demo header"]
    for _ in range(n):
        x = 50 + rng.random() * 900
        y = 50 + rng.random() * 900
        r = 5 + rng.random() * 10
        rows.append(f"{x:.12e}  {y:.12e}  {r:.12e}")
    p.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return p


@pytest.fixture(autouse=True)
def _small_crop(monkeypatch):
    """缩小 CROP 视野到 1km×1km，测试秒级完成。"""
    monkeypatch.setattr(config, "CROP_MIN_X", 0.0)
    monkeypatch.setattr(config, "CROP_MAX_X", 1000.0)
    monkeypatch.setattr(config, "CROP_MIN_Y", 0.0)
    monkeypatch.setattr(config, "CROP_MAX_Y", 1000.0)


def test_arg_parser_options():
    p = build_arg_parser()
    args = p.parse_args(["--dirs", "a", "b", "--seed", "42", "--dry-run", "--out", "x.png"])
    assert args.dirs == ["a", "b"]
    assert args.seed == 42
    assert args.dry_run is True
    assert args.out == "x.png"
    assert p.parse_args([]).dirs is None


def test_main_version(capsys):
    assert main(["--version"]) == 0
    assert "zdem-dfn" in capsys.readouterr().out


def test_run_batch_empty_dirs(monkeypatch):
    monkeypatch.setattr(config, "TARGET_DIRECTORIES", [])
    assert run_batch() == 1


def test_run_batch_missing_reference(tmp_path):
    assert run_batch(directories=[str(tmp_path / "nonexistent")]) == 1


def test_run_batch_reference_without_particles(tmp_path, monkeypatch):
    (tmp_path / "ini_xyr.dat").write_text("# only headers\n", encoding="utf-8")
    assert run_batch(directories=[str(tmp_path)]) == 1


def test_run_batch_dry_run_writes_nothing(tmp_path, capsys):
    p = _make_specimen(tmp_path)
    before = p.read_text(encoding="utf-8")
    rc = run_batch(directories=[str(tmp_path)], seed=42, dry_run=True)
    assert rc == 0
    assert p.read_text(encoding="utf-8") == before  # 就地覆写被跳过
    assert not (tmp_path / "dfn_preview.png").exists()


def test_run_batch_end_to_end(tmp_path):
    """全管线：覆写文件、tab 标签后缀、预览图落地。"""
    p = _make_specimen(tmp_path)
    out = tmp_path / "render.png"
    rc = run_batch(directories=[str(tmp_path)], seed=42, out_image=str(out))
    assert rc == 0

    text = p.read_text(encoding="utf-8").splitlines()
    assert text[0] == "# synthetic test specimen"
    tagged = [line for line in text if "\tDFN_" in line]
    assert tagged, "应存在被裂隙切中的颗粒"
    for line in text[2:]:  # 粒行保持科学计数法
        assert "e+" in line.split("\t")[0]

    assert out.exists() and out.stat().st_size > 10_000


def test_run_batch_seed_reproducible(tmp_path):
    """同 seed 两次运行 → 覆写文件逐字节一致。"""
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    _make_specimen(a)
    _make_specimen(b)
    run_batch(directories=[str(a)], seed=123, out_image=str(tmp_path / "a.png"))
    run_batch(directories=[str(b)], seed=123, out_image=str(tmp_path / "b.png"))
    assert a.joinpath("ini_xyr.dat").read_bytes() == b.joinpath("ini_xyr.dat").read_bytes()


def test_run_batch_skips_missing_subfolder(tmp_path, capsys):
    """多目录批处理：缺失子目录跳过不致命。"""
    good = tmp_path / "good"
    good.mkdir()
    _make_specimen(good)
    rc = run_batch(directories=[str(good), str(tmp_path / "missing")],
                   seed=42, out_image=str(tmp_path / "out.png"))
    assert rc == 0
    captured = capsys.readouterr().out
    assert "找不到指定的围压容器文件夹" in captured
    assert (tmp_path / "out.png").exists()


def test_main_cli_dispatch(tmp_path):
    """python -m zdem_dfn 等价的 main() 调度路径。"""
    _make_specimen(tmp_path)
    rc = main(["--dirs", str(tmp_path), "--seed", "5",
               "--out", str(tmp_path / "cli.png")])
    assert rc == 0
    assert (tmp_path / "cli.png").exists()
