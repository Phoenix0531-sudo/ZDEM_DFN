# ZDEM DFN

Discrete fracture network (DFN) generator for ZDEM discrete element
simulations: multi-set stochastic networks with seeded reproducibility,
hash-grid-accelerated particle–fracture tagging, and preview rendering.

![dfn_preview.png rendered from synthetic demo data](screenshots/dfn_preview_demo.png)

## Install

```bash
pip install git+https://github.com/Phoenix0531-sudo/ZDEM_DFN.git
# or clone and install from source:
#   git clone https://github.com/Phoenix0531-sudo/ZDEM_DFN && pip install .
```

## Quick start

```bash
# bundled synthetic demo (not laboratory data):
python -m zdem_dfn --input examples/demo_case --output outputs/demo_case --seed 42

# inspect without creating output:
python -m zdem_dfn --input examples/demo_case --output outputs/demo_case --dry-run
```

The output directory contains `ini_xyr_dfn.dat` and `dfn_preview.png`; the
source file is preserved. See [Usage](usage.md) and [Data format](data-format.md)
for the compatibility batch interface and input details.

All images on this site are generated from **synthetic demo data** —
never laboratory measurements.

## Start here

- [Usage](usage.md) — CLI reference, fracture-set configuration, examples.
- [Data format](data-format.md) — `ini_xyr.dat` fields, units and output layout.
- [Code reference](reference/zdem_dfn/config.md) — auto-generated API docs.
