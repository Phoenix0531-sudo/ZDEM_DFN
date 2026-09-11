"""Regenerate the README preview image from 100% synthetic data.

Steps performed by this script:

1. Generate a synthetic ``ini_xyr.dat`` specimen: a jittered, staggered
   (near-packed) particle assembly in the exact format the engine parses —
   whitespace-separated ``x y r`` rows in scientific notation, arbitrary
   non-numeric lines preserved as headers.
2. Run the real CLI entry point (equivalent to
   ``python -m zdem_dfn --dirs <specimen> --out <png> --seed …``) over it
   with a fixed seed, producing ``dfn_preview.png``.

    python examples/synthetic_demo.py
    python examples/synthetic_demo.py --out-dir somewhere

The committed ``docs/screenshots/dfn_preview_demo.png`` was produced by
exactly this script with its default parameters.

The data is SYNTHETIC — it is not laboratory output and implies no
measured specimen. Coordinates live inside the engine's CROP window so
every particle renders.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import tempfile

os.environ.setdefault("MPLBACKEND", "Agg")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # repo root, for in-repo runs

from zdem_dfn import config  # noqa: E402
from zdem_dfn.main import main as cli_main  # noqa: E402

SEED = 20240613  # identical to the run that produced the committed preview

# Model window mirrors the CROP_* constants so every particle is visible.
X0, X1 = config.CROP_MIN_X, config.CROP_MAX_X
Y0, Y1 = config.CROP_MIN_Y, config.CROP_MAX_Y

R_MIN, R_MAX = 25.0, 32.0   # particle radii -> avg diameter ~57
SPACING = 66.0              # ~ max diameter: near-touching assembly
ROW_GAP = 58.0              # staggered (hex-like) rows
JITTER = 3.0
MARGIN = 80.0


def generate_specimen(specimen_dir: str) -> str:
    """Write a synthetic ini_xyr.dat; return its path."""
    rng = random.Random(SEED)
    rows = []
    y = Y0 - MARGIN
    row = 0
    while y <= Y1 + MARGIN:
        xoff = (SPACING / 2.0) if row % 2 else 0.0
        x = X0 - MARGIN + xoff
        while x <= X1 + MARGIN:
            rows.append((
                x + rng.uniform(-JITTER, JITTER),
                y + rng.uniform(-JITTER, JITTER),
                rng.uniform(R_MIN, R_MAX),
            ))
            x += SPACING
        y += ROW_GAP
        row += 1

    os.makedirs(specimen_dir, exist_ok=True)
    out = os.path.join(specimen_dir, "ini_xyr.dat")
    with open(out, "w", encoding="utf-8") as f:
        f.write("# synthetic demo specimen for ZDEM_DFN preview (NOT lab data)\n")
        f.write(f"# particles: {len(rows)} window: [{X0:.0f},{X1:.0f}]x[{Y0:.0f},{Y1:.0f}]\n")
        for px, py, pr in rows:
            f.write(f"{px:.12e}  {py:.12e}  {pr:.12e}\n")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out-dir", default=os.path.join(tempfile.gettempdir(), "zdem_dfn_demo"),
        help="directory for the specimen + preview (default: system temp)")
    args = parser.parse_args()

    specimen = generate_specimen(args.out_dir)
    print(f"[1/2] wrote {specimen}")

    png = os.path.join(args.out_dir, "dfn_preview.png")
    rc = cli_main(["--dirs", args.out_dir, "--out", png, "--seed", str(SEED)])
    if rc == 0:
        # Optimize for docs embedding: matplotlib writes raw RGBA (~2.5 MB);
        # the plot uses few flat colors, so a deterministic 256-color palette
        # PNG loses nothing visible and is ~4x lighter. Pillow ships with
        # matplotlib, so no extra dependency is introduced.
        from PIL import Image

        raw = os.path.join(args.out_dir, "dfn_preview_raw.png")
        os.replace(png, raw)
        Image.open(raw).convert("P", palette=Image.ADAPTIVE, colors=256).save(
            png, optimize=True)
        os.remove(raw)
    print(f"[2/2] rc={rc} -> {png} (synthetic data only, not lab output)")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
