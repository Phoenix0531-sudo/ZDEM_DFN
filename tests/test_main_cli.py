"""CLI 与批处理编排测试：退出码、dry-run、端到端管线、种子复现。"""
import random

import pytest

from zdem_dfn import config
from zdem_dfn.main import build_arg_parser, main, run_batch


def test_dunder_main_module_entry(tmp_path, monkeypatch):
    """python -m zdem_dfn 入口：__main__.py 的 main 代理与 SystemExit 语义。"""
    import subprocess
    import sys

    _make_specimen(tmp_path)
    monkeypatch.chdir(tmp_path)
    proc = subprocess.run(
        [sys.executable, "-m", "zdem_dfn", "--dirs", str(tmp_path),
         "--seed", "7", "--out", str(tmp_path / "m.png")],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "m.png").exists()


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
    """全管线：非破坏性写 ini_xyr_dfn.dat、源文件不动、tab 标签后缀、预览图落地。"""
    p = _make_specimen(tmp_path)
    src_before = p.read_text(encoding="utf-8")
    out = tmp_path / "render.png"
    rc = run_batch(directories=[str(tmp_path)], seed=42, out_image=str(out))
    assert rc == 0

    # 源文件保持不动
    assert p.read_text(encoding="utf-8") == src_before

    tagged_file = tmp_path / "ini_xyr_dfn.dat"
    assert tagged_file.exists(), "默认应写 <stem>_dfn<ext>，而非覆写源文件"
    text = tagged_file.read_text(encoding="utf-8").splitlines()
    assert text[0] == "# synthetic test specimen"
    tagged = [line for line in text if "\tDFN_" in line]
    assert tagged, "应存在被裂隙切中的颗粒"
    for line in text[2:]:  # 粒行保持科学计数法
        assert "e+" in line.split("\t")[0]

    assert out.exists() and out.stat().st_size > 10_000


def test_run_batch_seed_reproducible(tmp_path):
    """同 seed 两次运行 → 输出文件逐字节一致。"""
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    _make_specimen(a)
    _make_specimen(b)
    run_batch(directories=[str(a)], seed=123, out_image=str(tmp_path / "a.png"))
    run_batch(directories=[str(b)], seed=123, out_image=str(tmp_path / "b.png"))
    assert a.joinpath("ini_xyr_dfn.dat").read_bytes() == b.joinpath("ini_xyr_dfn.dat").read_bytes()


def test_run_batch_skips_missing_subfolder(tmp_path, capsys):
    """多目录批处理：缺失子目录跳过不致命。"""
    good = tmp_path / "good"
    good.mkdir()
    _make_specimen(good)
    rc = run_batch(directories=[str(good), str(tmp_path / "missing")],
                   seed=42, out_image=str(tmp_path / "out.png"))
    assert rc == 0
    captured = capsys.readouterr().out
    assert "目录不存在" in captured
    assert (tmp_path / "out.png").exists()


def test_run_batch_stats_report(tmp_path):
    """--stats 写 Markdown 报告，含 p21 对比与分箱表。"""
    _make_specimen(tmp_path)
    rc = run_batch(directories=[str(tmp_path)], seed=7,
                   out_image=str(tmp_path / "out.png"),
                   stats_path=str(tmp_path / "stats.md"))
    assert rc == 0
    text = (tmp_path / "stats.md").read_text(encoding="utf-8")
    assert "p21" in text and "方向角分布" in text and "迹长分布" in text
    assert "达成率" in text


def test_main_cli_stats_flag(tmp_path):
    """CLI --stats 生效（.csv → CSV）。"""
    _make_specimen(tmp_path)
    rc = main(["--dirs", str(tmp_path), "--seed", "7",
               "--out", str(tmp_path / "out.png"),
               "--stats", str(tmp_path / "stats.csv")])
    assert rc == 0
    text = (tmp_path / "stats.csv").read_text(encoding="utf-8")
    assert "p21_actual" in text and "dip_bin_deg" in text


def test_main_cli_rose_flag(tmp_path):
    """CLI --rose 生成玫瑰图 PNG（含深红柱体）。"""
    from PIL import Image

    _make_specimen(tmp_path)
    rose = tmp_path / "rose.png"
    rc = main(["--dirs", str(tmp_path), "--seed", "7",
               "--out", str(tmp_path / "out.png"),
               "--rose", str(rose)])
    assert rc == 0
    assert rose.exists()
    im = Image.open(str(rose)).convert("RGB")
    colors = im.getcolors(maxcolors=10_000_000)
    dark_red = sum(c for c, (r, g, b) in colors if r > 90 and g < 70 and b < 70)
    assert dark_red > 500, dark_red


def test_main_cli_rose_with_dry_run(tmp_path):
    """--dry-run 下 --rose 仍产出分析图（不写模型文件）。"""
    _make_specimen(tmp_path)
    rc = main(["--dirs", str(tmp_path), "--seed", "7",
               "--dry-run", "--rose", str(tmp_path / "rose.png")])
    assert rc == 0
    assert (tmp_path / "rose.png").exists()
    assert not (tmp_path / "ini_xyr_dfn.dat").exists()  # 不写模型输出


def test_main_cli_dispatch(tmp_path):
    """python -m zdem_dfn 等价的 main() 调度路径。"""
    _make_specimen(tmp_path)
    rc = main(["--dirs", str(tmp_path), "--seed", "5",
               "--out", str(tmp_path / "cli.png")])
    assert rc == 0
    assert (tmp_path / "cli.png").exists()


def test_run_batch_in_place_overwrites(tmp_path):
    """--in-place：恢复旧版覆写语义，不产生 _dfn 文件。"""
    p = _make_specimen(tmp_path)
    src_before = p.read_text(encoding="utf-8")
    rc = run_batch(directories=[str(tmp_path)], seed=42,
                   out_image=str(tmp_path / "x.png"), in_place=True)
    assert rc == 0
    assert p.read_text(encoding="utf-8") != src_before, "源文件应被覆写"
    assert "\tDFN_" in p.read_text(encoding="utf-8")
    assert not (tmp_path / "ini_xyr_dfn.dat").exists()


def test_run_batch_custom_suffix(tmp_path):
    """--suffix 自定义：写 ini_xyr.tagged.dat。"""
    _make_specimen(tmp_path)
    rc = run_batch(directories=[str(tmp_path)], seed=42,
                   out_image=str(tmp_path / "x.png"), suffix=".tagged")
    assert rc == 0
    assert (tmp_path / "ini_xyr.tagged.dat").exists()
    assert (tmp_path / "ini_xyr.dat").exists()


def test_main_empty_suffix_without_in_place_refused(tmp_path, capsys):
    """--suffix '' 且未传 --in-place → argparse error（exit 2），不碰任何文件。"""
    _make_specimen(tmp_path)
    src_before = (tmp_path / "ini_xyr.dat").read_text(encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        main(["--dirs", str(tmp_path), "--suffix", ""])
    assert exc_info.value.code == 2
    assert (tmp_path / "ini_xyr.dat").read_text(encoding="utf-8") == src_before


def test_main_in_place_empty_suffix_allowed(tmp_path):
    """--in-place --suffix ''：显式覆写语义，合法。"""
    _make_specimen(tmp_path)
    rc = main(["--dirs", str(tmp_path), "--in-place", "--suffix", "",
               "--seed", "42", "--out", str(tmp_path / "y.png")])
    assert rc == 0
    assert "\tDFN_" in (tmp_path / "ini_xyr.dat").read_text(encoding="utf-8")


def test_dry_run_leaves_source_untouched_any_mode(tmp_path):
    """dry-run：两种模式下源文件都分毫不动，且无输出文件产生。"""
    p = _make_specimen(tmp_path)
    src_before = p.read_text(encoding="utf-8")
    assert run_batch(directories=[str(tmp_path)], seed=1, dry_run=True) == 0
    assert run_batch(directories=[str(tmp_path)], seed=1, dry_run=True,
                     in_place=True) == 0
    assert p.read_text(encoding="utf-8") == src_before
    assert not (tmp_path / "ini_xyr_dfn.dat").exists()
