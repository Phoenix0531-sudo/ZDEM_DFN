"""预览图渲染测试：动态刻度随 CROP 窗口缩放，不再悬空。"""
import matplotlib

matplotlib.use("Agg")

from zdem_dfn import config
from zdem_dfn.plotting import generate_preview_plot, plot_rose_diagram
from zdem_dfn.stats import compute_dip_bins


def _particles(n=6, seed=3):
    import random
    rng = random.Random(seed)
    return [{"type": "particle", "x": float(50 + rng.random() * 900),
             "y": float(50 + rng.random() * 900),
             "r": float(5 + rng.random() * 10), "tag": None} for _ in range(n)]


FRACTURES = [((100.0, 100.0), (900.0, 900.0))]


def _render_and_get_ticks(tmp_path, monkeypatch):
    """渲染后截获 fig（禁用 close），返回 (xticks, yticks)。"""
    import matplotlib.pyplot as plt
    monkeypatch.setattr(plt, "close", lambda *a, **k: None)
    generate_preview_plot(_particles(), FRACTURES, 0.0, 1000.0, 0.0, 1000.0,
                          out_path=str(tmp_path / "t.png"))
    fig = plt.gcf()
    ax = fig.axes[0]
    xt, yt = list(ax.get_xticks()), list(ax.get_yticks())
    plt.close("all")
    return xt, yt


def test_small_window_ticks_in_range(tmp_path, monkeypatch):
    """CROP 改为 1km×1km 后，实际渲染刻度必须落在窗口内（旧版悬空到 3000+）。"""
    monkeypatch.setattr(config, "CROP_MIN_X", 0.0)
    monkeypatch.setattr(config, "CROP_MAX_X", 1000.0)
    monkeypatch.setattr(config, "CROP_MIN_Y", 0.0)
    monkeypatch.setattr(config, "CROP_MAX_Y", 1000.0)
    xt, yt = _render_and_get_ticks(tmp_path, monkeypatch)
    assert xt and all(0.0 <= t <= 1000.0 for t in xt), xt
    assert yt and all(0.0 <= t <= 1000.0 for t in yt), yt
    assert xt[-1] == 1000.0  # 首尾触边
    assert yt[-1] == 1000.0


def test_default_window_ticks_match_default_crop(tmp_path, monkeypatch):
    """默认 CROP（2000-6000 × 3000-11000）下刻度覆盖窗口、首尾触边。"""
    xt, yt = [], []
    import matplotlib.pyplot as plt
    monkeypatch.setattr(plt, "close", lambda *a, **k: None)
    # 粒子放在默认窗口内
    import random
    rng = random.Random(3)
    parts = [{"type": "particle", "x": float(2100 + rng.random() * 3800),
              "y": float(3100 + rng.random() * 7800),
              "r": float(5 + rng.random() * 10), "tag": None} for _ in range(6)]
    generate_preview_plot(parts, FRACTURES,
                          config.CROP_MIN_X, config.CROP_MAX_X,
                          config.CROP_MIN_Y, config.CROP_MAX_Y,
                          out_path=str(tmp_path / "d.png"))
    fig = plt.gcf()
    ax = fig.axes[0]
    xt, yt = list(ax.get_xticks()), list(ax.get_yticks())
    plt.close("all")
    assert xt[0] == config.CROP_MIN_X and xt[-1] == config.CROP_MAX_X
    assert yt[0] == config.CROP_MIN_Y and yt[-1] == config.CROP_MAX_Y
    assert len(xt) == 5  # 4 等分
    assert len(yt) == 9  # 8 等分


def test_rose_diagram_writes_png(tmp_path):
    """玫瑰图：两批正交裂隙（45°/135°），PNG 非空白且含深红柱。"""
    from PIL import Image

    # 45° 与 135° 各 4 条，同长度
    fractures = [((0.0, 0.0), (10.0, 10.0))] * 4 + [((0.0, 10.0), (10.0, 0.0))] * 4
    out = str(tmp_path / "rose.png")
    plot_rose_diagram(fractures, out, bin_size=10.0)

    im = Image.open(out).convert("RGB")
    assert im.size[0] > 100 and im.size[1] > 100
    colors = im.getcolors(maxcolors=10_000_000)
    dark_red = sum(c for c, (r, g, b) in colors if r > 90 and g < 70 and b < 70)
    white = sum(c for c, (r, g, b) in colors if r > 240 and g > 240 and b > 240)
    assert dark_red > 1000, dark_red   # 有柱体
    assert white > 1000                # 有留白


def test_rose_diagram_bins_match_stats(tmp_path):
    """玫瑰图扇区与统计报告分箱一致：45/135 各占一半。"""
    fractures = [((0.0, 0.0), (10.0, 10.0))] * 4 + [((0.0, 10.0), (10.0, 0.0))] * 4
    monkeyfig_path = str(tmp_path / "r2.png")

    import matplotlib.pyplot as _plt
    orig_close = _plt.close
    _plt.close = lambda *a, **k: None
    try:
        plot_rose_diagram(fractures, monkeyfig_path, bin_size=10.0)
        fig = _plt.gcf()
        ax = fig.axes[0]
        # 柱高总和 = 裂隙条数，两主峰各占 4
        heights = [b.get_height() for b in ax.patches]
        assert sum(heights) == 8
        assert max(heights) == 4
        bins = compute_dip_bins([45.0, 135.0] * 4)
        assert sum(bins) == 8 and max(bins) == 4
    finally:
        _plt.close = orig_close
        orig_close("all")
