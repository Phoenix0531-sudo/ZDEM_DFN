# ZDEM DFN

**Discrete Fracture Network generator for ZDEM particle packs**

[English](README.md) | [中文](README.zh-CN.md)

![CI](https://github.com/Phoenix0531-sudo/ZDEM_DFN/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

ZDEM DFN generates **discrete fracture networks** over ZDEM-style particle initial packs (`ini_xyr.dat`), for rock-mechanics / DEM pre-processing.

The engine is `zdem_dfn/engine.py` with multi-set fracture controls, optional heterogeneous modes, and matplotlib diagnostics. Console entry: `zdem-dfn` after install.

## Why this exists

Building DFN by hand inside each experiment folder does not scale. This package centralizes generation parameters and batch targets for ZDEM workflows.

## Features

- Read/write ZDEM-oriented particle init files
- Multiple fracture sets with length / orientation statistics
- Crop window for a “safe” generation region
- Progress via `tqdm`; optional matplotlib previews
- Installable console script `zdem-dfn`

## Install

```bash
git clone https://github.com/Phoenix0531-sudo/ZDEM_DFN.git
cd ZDEM_DFN
pip install -r requirements.txt
pip install -e .
```

## Usage

1. Point `TARGET_DIRECTORIES` / source filename constants in `zdem_dfn/engine.py` at your experiment folders (or call the engine API from a small driver script).
2. Run:

```bash
zdem-dfn
# or
python -m zdem_dfn.engine
```

Expect `ini_xyr.dat`-style inputs; adjust crop bounds (`CROP_MIN_X` …) to your model domain.

## Project layout

```
zdem_dfn/engine.py
setup.py            # entry point zdem-dfn
tests/
```

## Related ZDEM tools

| Repo | Role |
|------|------|
| [ZDEM_ParticleTracker](https://github.com/Phoenix0531-sudo/ZDEM_ParticleTracker) | Interactive particle tracking + VisPy true-radius render |
| [ZDEM_Salt_Kinematics](https://github.com/Phoenix0531-sudo/ZDEM_Salt_Kinematics) | Salt geometry / kinematics extraction & plots |
| [ZDEM_Area_Conservation](https://github.com/Phoenix0531-sudo/ZDEM_Area_Conservation) | Area-conservation / triangulation analysis |
| [ZDEM_Bond_Fracture](https://github.com/Phoenix0531-sudo/ZDEM_Bond_Fracture) | Bond damage series + desktop / CLI |
| [ZDEM_Damage_Thresholds](https://github.com/Phoenix0531-sudo/ZDEM_Damage_Thresholds) | Damage thresholds & strain–energy plots |
| [ZDEM_DFN](https://github.com/Phoenix0531-sudo/ZDEM_DFN) | Discrete fracture network generator for ZDEM |
| [ZDEM_Model_Editor](https://github.com/Phoenix0531-sudo/ZDEM_Model_Editor) | Model file visual editor |
| [ZDEM_Archiver](https://github.com/Phoenix0531-sudo/ZDEM_Archiver) | Purge / archive bulky simulation dumps |
| [ZDEM3D_WEB](https://github.com/Phoenix0531-sudo/ZDEM3D_WEB) | CAE cloud UI (Django + React + VTK.js) |
## License

MIT. Free for commercial use with attribution. See [LICENSE](LICENSE).
