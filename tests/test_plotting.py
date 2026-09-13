"""预览图渲染测试：动态刻度随 CROP 窗口缩放，不再悬空。"""
import matplotlib

matplotlib.use("Agg")

from zdem_dfn import config
from zdem_dfn.plotting import generate_preview_plot


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
