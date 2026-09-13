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
# batch-process specimen folders (each containing ini_xyr.dat):
python -m zdem_dfn --dirs path/to/spec1 path/to/spec2 --seed 42

# inspect without writing anything:
python -m zdem_dfn --dirs path/to/spec1 --dry-run
```

All images on this site are generated from **synthetic demo data** —
never laboratory measurements.

## Start here

- [Usage](usage.md) — CLI reference, fracture-set configuration, examples.
- [Code reference](reference/zdem_dfn/config.md) — auto-generated API docs.
