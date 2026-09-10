# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-09-09

### Added
- CLI entry point: `python -m zdem_dfn --dirs … --out … --seed … --dry-run --version`, replacing the hardcoded-constants-only workflow
- Single-responsibility module split: `config` / `geometry` / `dfn` / `io` / `sampling` / `plotting` / `main`, with `engine.py` kept as a compatibility facade re-exporting the original names
- Hash-grid accelerated particle–fracture intersection (replaces O(P×F) brute force; equivalence covered by tests)
- Unit test suite grew from 8 to 36 tests: parse roundtrip, seed reproducibility (byte-identical reruns), geometry semantics, grid-vs-bruteforce equivalence, CLI exit codes, end-to-end pipeline
- CI packaging job: wheel build → clean-venv install → module import smoke test

### Fixed
- `pyproject.toml` declared `py-modules = []`, which disabled auto-discovery and shipped an **empty wheel** — fresh `pip install zdem-dfn` yielded an unusable package; now declares `packages = ["zdem_dfn"]` explicitly
- `dfn.py` read the module-global `FRACTURE_SETS` directly, so runtime overrides of `zdem_dfn.config.FRACTURE_SETS` were silently ignored; now resolves through the config module, consistent with the facade contract
- Particle–fracture intersection now counts **every** intersecting fracture per particle (per-set semantics preserved) and includes exact boundary touches (`dist <= r`)

### Changed
- Version aligned to 1.1.0 across `pyproject.toml`, `__init__.__version__` and `uv.lock` (was inconsistent 0.1.0 / 1.0.0)
- READMEs (EN/中文) updated for the new module layout, CLI usage and `config.py` as the runtime override point; `docs/index.md` quick start refreshed

## [1.0.0] - 2026-06-08

### Added
- Initial public release
- first commit
