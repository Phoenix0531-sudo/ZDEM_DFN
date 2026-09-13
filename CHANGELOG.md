# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Network statistics reports** (`--stats PATH`): actual-vs-target p21 (total trace length / window area vs `sum(FRACTURE_SETS[].p21)`), a dip histogram binned every 10°, a 10-bin trace-length histogram; `.csv` suffix writes CSV, anything else writes Markdown. Works with `--dry-run`
- **Pyright type checking** in CI (`--level error` on the package) and an OS matrix (ubuntu-latest + windows-latest) for the test job

### Changed
- **Non-destructive output by default**: tagged particles are now written to `<stem><suffix><ext>` (`ini_xyr_dfn.dat` by default, configurable via `--suffix`) next to the source file; the source `ini_xyr.dat` is never modified unless `--in-place` is passed. An empty `--suffix` without `--in-place` is rejected (exit 2). This closes the last Tier-1 review blocker.
- Professional plain-language progress output (`[1/4]`–`[4/4]`, `[skip]`/`[missing]` markers) replaces the flowery engine banners (e.g. “地壳破碎再造引擎”)
- Removed leftover `typing.cast` workarounds from the module split

## [1.1.1] - 2026-09-12

### Added
- mkdocs-material documentation site (CLI guide, fracture-set configuration, auto-generated API reference) deployed to GitHub Pages on every push to `main`
- Coverage pipeline: pytest-cov job in CI (96% line coverage), XML artifact upload and a self-hosted shields badge on the `badges` branch
- Parameter gallery: `python examples/gallery.py` renders the same synthetic specimen under four `config.FRACTURE_SETS` configurations (embedded in both READMEs)
- Community health files: `CITATION.cff` (GitHub "Cite this repository"), `CONTRIBUTING.md`, `SECURITY.md`, issue templates (bug/feature), PR template
- Release workflow (`publish.yml`): builds sdist + wheel with `uv build` and attaches them to the GitHub Release on every version tag

### Changed
- `pyproject.toml` is now the single source of truth: real description, license/readme metadata, `zdem-dfn` console script, unified dev deps (pytest, pytest-cov, ruff); `setup.py` and `requirements.txt` removed
- Ruff rule set enforced repo-wide (E4/E7/E9/F/I/B/UP) with per-file ignores for the sys.path preamble in examples/tests; 13 findings fixed
- READMEs: coverage/docs badges, parameter gallery, documentation-site link, citation section, mermaid data-flow diagram

### Removed
- `docs/screenshots/preview.png` decorative schematic and `.gitkeep` placeholder — README now shows only genuine engine output

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
