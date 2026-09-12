#!/usr/bin/env python3
"""Render a 2x2 parameter-gallery panel of DFN networks (deterministic).

Each panel runs the *real* pipeline (generate_dfn_network -> tag -> plot)
on the same synthetic specimen with a different seed and fracture-set
configuration, showing how ``config.FRACTURE_SETS`` reshapes the network:

    (a) default sets, seed 42     (b) single steep joint set, seed 7
    (c) dense low-intensity web   (d) sparse long corridor faults, seed 3

    python examples/gallery.py [--out docs/screenshots/dfn_gallery.png]

Writes nothing else; the specimen is built in memory via the bundled
sampling/io helpers and never touches an ``ini_xyr.dat`` on disk.
"""

from __future__ import annotations

import argparse
import copy
import os
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # repo root, for in-repo runs

import matplotlib

matplotlib.use("Agg")

from zdem_dfn import config  # noqa: E402
from zdem_dfn.dfn import generate_dfn_network  # noqa: E402
from zdem_dfn.io import parse_particle_file  # noqa: E402
from zdem_dfn.sampling import apply_fracture_tagging  # noqa: E402

SPEC_LINES = [
    "# SYNTHETIC DEMO DATA (script-generated staggered packing; not laboratory data)",
    "# x y r particle rows in scientific notation",
]


def make_specimen_text(x0: float, x1: float, y0: float, y1: float,
                       pitch: float = 66.0, row_gap: float = 58.0,
                       r_lo: float = 25.0, r_hi: float = 32.0) -> str:
    """Staggered near-packed particle lattice over [x0,x1]x[y0,y1]."""
    rng = random.Random(20240613)
    lines = list(SPEC_LINES)
    y = y0 - 80.0
    row = 0
    while y < y1 + 80.0:
        offset = (pitch / 2.0) if (row % 2) else 0.0
        x = x0 - 80.0 + offset
        while x < x1 + 80.0:
            r = rng.uniform(r_lo, r_hi)
            lines.append(f"{x + rng.uniform(-3, 3):.12e}  "
                         f"{y + rng.uniform(-3, 3):.12e}  {r:.12e}")
            x += pitch
        y += row_gap
        row += 1
    return "\n".join(lines) + "\n"


def _parse_specimen(text: str):
    """parse_particle_file takes a path, so stage the in-memory specimen."""
    fd, tmp = tempfile.mkstemp(suffix=".dat", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        return parse_particle_file(tmp)
    finally:
        os.unlink(tmp)


def render_panel(ax, lines_text: str, sets: list[dict], seed: int, label: str) -> None:
    """One gallery panel: seeded network for the given fracture sets."""
    from matplotlib.collections import LineCollection, PatchCollection
    from matplotlib.patches import Circle

    data = _parse_specimen(lines_text)
    particles = [d for d in data if d.get("type") == "particle"]
    x0, x1 = config.CROP_MIN_X, config.CROP_MAX_X
    y0, y1 = config.CROP_MIN_Y, config.CROP_MAX_Y
    area = (x1 - x0) * (y1 - y0)

    diameter = 2.0 * sum(p["r"] for p in particles) / len(particles)
    ref_len = diameter * max(float(s["length_mult"]) for s in sets)
    grid_cell = ref_len * 1.5
    max_r = max(p["r"] for p in particles)

    random.seed(seed)
    segments, _ = generate_dfn_network(area, x0, x1, y0, y1, diameter)

    # Tagging is display-only here; restore the config the pipeline ships with.
    saved_sets, config.FRACTURE_SETS = config.FRACTURE_SETS, sets
    try:
        apply_fracture_tagging(particles, segments, grid_cell, max_r)
    finally:
        config.FRACTURE_SETS = saved_sets

    colors = {"Background": "#E0E0E0", "DFN_Matrix": "#A6C4D9",
              "DFN_Asperity": "#32CD32", "DFN_Gouge": "#DC143C", "DFN_Node": "#000000"}
    by_tag: dict[str, list] = {}
    for p in particles:
        by_tag.setdefault(p.get("tag", "Background"), []).append(p)

    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_facecolor("white")
    for tag, members in by_tag.items():
        coll = PatchCollection(
            [Circle((m["x"], m["y"]), m["r"]) for m in members],
            facecolor=colors.get(tag, "#E0E0E0"), edgecolor="none")
        ax.add_collection(coll)
    if segments:
        ax.add_collection(LineCollection(segments, colors="#8B0000", linewidths=1.0))
    ax.set_title(f"({label})", loc="left", fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])


def main() -> int:
    ap = argparse.ArgumentParser(description="render the 2x2 DFN parameter gallery")
    ap.add_argument("--out", default=str(HERE.parent / "docs" / "screenshots" / "dfn_gallery.png"))
    args = ap.parse_args()

    import matplotlib.pyplot as plt

    x0, x1 = config.CROP_MIN_X, config.CROP_MAX_X
    y0, y1 = config.CROP_MIN_Y, config.CROP_MAX_Y
    specimen = make_specimen_text(x0, x1, y0, y1)

    default_sets = copy.deepcopy(config.FRACTURE_SETS)

    panels = [
        ("a", default_sets, 42),
        ("b", [{
            "set_name": "Steep_Joints",
            "p21": 0.002,
            "length_mult": 4.0,
            "length_std_ratio": 0.2,
            "dip_mean": 80.0,
            "dip_std": 3.0,
            "truncation_prob": 0.0,
        }], 7),
        ("c", [
            {"set_name": "Web_A", "p21": 0.0016, "length_mult": 2.5,
             "length_std_ratio": 0.4, "dip_mean": 30.0, "dip_std": 8.0,
             "truncation_prob": 0.5},
            {"set_name": "Web_B", "p21": 0.0016, "length_mult": 2.5,
             "length_std_ratio": 0.4, "dip_mean": -30.0, "dip_std": 8.0,
             "truncation_prob": 0.5},
            {"set_name": "Web_C", "p21": 0.0012, "length_mult": 2.0,
             "length_std_ratio": 0.5, "dip_mean": 0.0, "dip_std": 10.0,
             "truncation_prob": 0.5},
        ], 11),
        ("d", [{
            "set_name": "Corridor_Faults",
            "p21": 0.0004,
            "length_mult": 18.0,
            "length_std_ratio": 0.08,
            "dip_mean": 60.0,
            "dip_std": 2.0,
            "truncation_prob": 0.0,
        }], 3),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(10, 20), dpi=150)
    for ax, (label, sets, seed) in zip(axes.flat, panels, strict=True):
        render_panel(ax, specimen, sets, seed, label)

    fig.suptitle(
        "One specimen, different fracture-set configurations (all synthetic demo data)",
        fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
