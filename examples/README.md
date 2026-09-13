# Examples

## `synthetic_demo.py` — reproduce the README preview

Regenerates `docs/screenshots/dfn_preview_demo.png` end-to-end from
**100% synthetic data** (no laboratory measurements involved):

```bash
python examples/synthetic_demo.py                  # output to system temp
python examples/synthetic_demo.py --out-dir DIR    # or anywhere you like
```

What it does:

1. writes a jittered, staggered particle assembly as `ini_xyr.dat`
   (`x y r` rows in scientific notation — the exact format the engine
   parses), spanning the engine's CROP window;
2. runs the real CLI over it with a fixed seed (20240613), producing
   `dfn_preview.png` and a tagged output file in the temporary output folder;
3. palette-optimizes the PNG for docs embedding (deterministic, ~0.5 MB).

Re-running with the same package version reproduces the committed image
byte-for-byte. The committed copy was produced with the current v1.2.0 code.

> **Disclaimer**: the specimen is synthetic demo data — it is not
> laboratory output and implies no measured rock sample.

## `benchmark_sampling.py` — hash-grid vs brute force

Measures the particle–fracture intersection acceleration introduced in
v1.1 (see module `zdem_dfn.sampling`):

```bash
python examples/benchmark_sampling.py
```
