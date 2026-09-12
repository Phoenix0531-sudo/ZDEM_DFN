# Contributing to ZDEM DFN

Thanks for your interest in improving this project!

## Development setup

```bash
git clone https://github.com/Phoenix0531-sudo/ZDEM_DFN.git
cd ZDEM_DFN
python -m venv .venv
.venv\Scripts\activate        # Windows  (source .venv/bin/activate on Unix)
pip install -e ".[dev]"

# run the test suite
pytest tests/ -q
```

## Ground rules

- **All committed preview images are synthetic.** Never commit data from
  laboratory experiments. If a figure helps, generate it with
  `examples/gallery.py` or `python -m zdem_dfn` on synthetic specimens.
- **`zdem_dfn/config.py` is the single source of truth** for constants and
  toggles. Read config values through the module (`config.CROP_MIN_X`) so
  runtime overrides keep working; do not `from config import CROP_MIN_X`.
- Keep modules single-responsibility (see the README package-layout table).
  New behavior belongs in the module that owns that concern.

## Pull requests

1. Fork, then create a feature branch (`git checkout -b feat/my-change`).
2. Add or update tests for any behavior change — bug fixes need a
   regression test that fails without the fix.
3. `pytest tests/ -q` must pass and `ruff check .` should be clean.
4. Update `CHANGELOG.md` under **[Unreleased]**.
5. Keep the bilingual READMEs (`README.md`, `README.zh-CN.md`) consistent
   when user-facing behavior changes.
6. Open the PR against `main` with a short description of *what* and *why*.

## Reporting bugs

Open an issue with the bug report template. Include your Python version,
OS, and the command you ran (plus `--dry-run` output if relevant).
Do **not** paste proprietary experiment data or paths containing
confidential information.

## Proposing features

Open a feature-request issue describing the geoscience use case first —
the maintenance bar is "does this help ZDEM model workflows?" — then we
agree the interface before any code lands.
