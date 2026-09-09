# ZDEM DFN

Discrete Fracture Network generator for ZDEM simulations.

## Quick Start

```bash
pip install -r requirements.txt

# process specimen folders (each containing ini_xyr.dat):
python -m zdem_dfn --dirs path/to/spec1 path/to/spec2 --seed 42

# or dry-run to validate without writing anything:
python -m zdem_dfn --dirs path/to/spec1 --dry-run
```

See the [main README](../README.md) for configuration (`zdem_dfn/config.py`),
module layout, and preview images.

## License

MIT License
