#!/usr/bin/env python3
"""Benchmark: hash-grid acceleration vs brute-force intersection search.

The engine (``zdem_dfn.sampling``) uses a coarse hash grid to shortlist
candidate particles around each fracture segment and then performs exact
point-to-segment distance tests.  ``process_single_folder_lines`` in the
same module is the equivalent brute-force path (every particle x every
segment), kept as the acceleration baseline.

    python examples/benchmark_sampling.py
    python examples/benchmark_sampling.py --particles 20000 --segments 400

The script is read-only (writes nothing) and self-contained: it builds
particles in memory (no ``ini_xyr.dat`` files), seeds fractures with
``generate_dfn_network`` plus random top-up segments, and times both paths
on identical inputs.  Expected result: the hash grid wins by a wide
margin once the window is large relative to the search radius.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # repo root, for in-repo runs

from zdem_dfn import config  # noqa: E402
from zdem_dfn.dfn import generate_dfn_network  # noqa: E402
from zdem_dfn.sampling import apply_fracture_tagging, process_single_folder_lines  # noqa: E402

SEED = 20240613


def build_particles(n: int, rng: random.Random) -> list[dict]:
    """Uniform random particles over the CROP window, dict rows shaped like
    ``zdem_dfn.io.parse_particle_file`` output (type/x/y/r)."""
    x0, x1 = config.CROP_MIN_X, config.CROP_MAX_X
    y0, y1 = config.CROP_MIN_Y, config.CROP_MAX_Y
    return [
        {
            "type": "particle",
            "x": rng.uniform(x0, x1),
            "y": rng.uniform(y0, y1),
            "r": rng.uniform(25.0, 32.0),
        }
        for _ in range(n)
    ]


def build_segments(total: int) -> list:
    """Seeded DFN from the engine generator, topped up with random segments."""
    x0, x1 = config.CROP_MIN_X, config.CROP_MAX_X
    y0, y1 = config.CROP_MIN_Y, config.CROP_MAX_Y
    area = (x1 - x0) * (y1 - y0)
    avg_diameter = 57.0  # matches the radii band above (25..32)

    random.seed(SEED)  # generate_dfn_network consumes the global random module
    segments, _ = generate_dfn_network(area, x0, x1, y0, y1, avg_diameter)

    rng = random.Random(SEED + 1)
    while len(segments) < total:
        cx = rng.uniform(x0, x1)
        cy = rng.uniform(y0, y1)
        ang = rng.uniform(0.0, math.pi)
        half = rng.uniform(40.0, 400.0)
        dx = half * math.cos(ang)
        dy = half * math.sin(ang)
        segments.append(((cx - dx, cy - dy), (cx + dx, cy + dy)))
    return segments[:total]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="benchmark hash-grid sampling vs brute-force intersection search")
    ap.add_argument("--particles", type=int, default=10000,
                    help="number of synthetic particles (default 10000)")
    ap.add_argument("--segments", type=int, default=400,
                    help="total fracture segments for both methods (default 400)")
    ap.add_argument("--repeats", type=int, default=3,
                    help="timing repeats per method, best-of (default 3)")
    args = ap.parse_args()

    # Same grid-size convention as the engine pipeline (zdem_dfn.main):
    # 1.5 x reference trace length derived from avg particle diameter.
    avg_diameter = 57.0
    reference_length = avg_diameter * float(config.FRACTURE_SETS[0]["length_mult"])
    grid_cell = reference_length * 1.5
    max_r = 32.0

    rng = random.Random(SEED)
    particles = build_particles(args.particles, rng)
    segments = build_segments(args.segments)

    x_span = config.CROP_MAX_X - config.CROP_MIN_X
    y_span = config.CROP_MAX_Y - config.CROP_MIN_Y
    print(f"particles={len(particles)}  segments={len(segments)}  "
          f"window={x_span:.0f}x{y_span:.0f}  grid_cell={grid_cell:.0f}")

    # --- brute force: every particle x every segment --------------------
    best_bf = float("inf")
    for _ in range(args.repeats):
        fresh = [dict(p) for p in particles]
        t0 = time.perf_counter()
        process_single_folder_lines(segments, fresh)
        best_bf = min(best_bf, time.perf_counter() - t0)

    # --- hash grid: shortlist candidate cells, then exact distance ------
    best_hg = float("inf")
    for _ in range(args.repeats):
        fresh = [dict(p) for p in particles]
        t0 = time.perf_counter()
        apply_fracture_tagging(fresh, segments, grid_cell, max_r)
        best_hg = min(best_hg, time.perf_counter() - t0)

    speedup = best_bf / best_hg if best_hg > 0 else float("inf")
    print(f"brute force : {best_bf * 1000:10.1f} ms")
    print(f"hash grid   : {best_hg * 1000:10.1f} ms")
    print(f"speedup     : {speedup:10.1f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
