# Usage

## CLI

```
python -m zdem_dfn --input DIR --output DIR [--seed SEED]
                   [--dry-run] [--verbose] [--stats PATH] [--rose PATH]

# compatibility batch interface:
python -m zdem_dfn [--dirs DIR [DIR ...]] [--out PATH] [--seed SEED]
                   [--suffix STR] [--in-place] [--dry-run] [--stats PATH] [--rose PATH] [--version]
```

Output is **non-destructive** by default: tagged particles are written to
`<stem><suffix><ext>` next to the source file (default suffix `_dfn` →
`ini_xyr_dfn.dat`); the source `ini_xyr.dat` is never modified unless
`--in-place` is passed. An empty `--suffix` is refused without `--in-place`
because it would silently overwrite the source.

| Flag | Meaning |
|---|---|
| `--input DIR` | Recommended single-case input folder containing `ini_xyr.dat`; use with `--output` |
| `--output DIR` | Recommended output folder; created automatically and receives all artifacts |
| `--dirs DIR [DIR …]` | Compatibility batch interface for one or more folders |
| `--out PATH` | Compatibility preview image output path |
| `--seed N` | RNG seed — same seed, same network |
| `--suffix STR` | Output filename suffix (default `_dfn` → `ini_xyr_dfn.dat`); empty string requires `--in-place` |
| `--in-place` | Overwrite the source file (legacy behavior; off by default) |
| `--dry-run` | Validate and print the plan; write no files or images |
| `--stats PATH` | Write a network statistics report (`.csv` → CSV, otherwise Markdown); skipped during `--dry-run` |
| `--rose PATH` | Write a polar rose diagram (PNG) of fracture strike; skipped during `--dry-run` |
| `--version` | Print the version and exit |

Exit codes: `0` success, `1` configuration error (no directories / missing
reference file / no valid particles), `2` invalid argument combination (empty
`--suffix` without `--in-place`).

## Input and output format

See [Data format](data-format.md) for the supported `ini_xyr.dat` records,
units, directory layout, output files and synthetic-demo disclaimer.

## Fracture-set configuration

Each entry in `zdem_dfn/config.FRACTURE_SETS` defines one orientation family:

```python
{
    "set_name": "Secondary_Joints",  # family name
    "p21": 0.001,                    # trace intensity: m of trace per m² of area
    "length_mult": 3.0,              # mean length = average particle diameter × mult
    "length_std_ratio": 0.3,         # log-normal spread (σ/μ)
    "dip_mean": -45.0,               # dip in degrees (sign sets the sense)
    "dip_std": 5.0,
    "truncation_prob": 0.90,         # chance of being truncated by a longer set
}
```

Longer sets truncate shorter ones (T-intersections). Add, remove or reweight
entries to compose conjugate patterns.

## Examples

### Parameter gallery

```bash
python examples/gallery.py --out docs/screenshots/dfn_gallery.png
```

Renders the same synthetic specimen under four fracture-set configurations
(default, single steep set, dense web, sparse corridor faults):

![DFN parameter gallery](screenshots/dfn_gallery.png)

### Hash-grid vs brute-force benchmark

```bash
python examples/benchmark_sampling.py
```

Hash-grid tagging beats the O(P×F) brute-force search (~11× at 10 000
particles × 400 segments) with tested tag equivalence.

### Programmatic use

```python
import random
import zdem_dfn.config as config
from zdem_dfn.main import run_batch

config.TARGET_DIRECTORIES = ["path/to/specimen"]  # runtime override
random.seed(42)
run_batch()
```

!!! note
    Read config values through the module (`config.CROP_MIN_X`), never
    `from config import CROP_MIN_X`, so runtime overrides keep working.
