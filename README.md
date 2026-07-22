# ZDEM DFN

**Discrete Fracture Network generators for ZDEM model workflows.**

[English](README.md) | [中文](README.zh-CN.md)

[![CI](https://github.com/Phoenix0531-sudo/ZDEM_DFN/actions/workflows/ci.yml/badge.svg)](https://github.com/Phoenix0531-sudo/ZDEM_DFN/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Build stochastic or controlled **fracture sets** and export conventions oriented to ZDEM model ingestion. Package lives under `zdem_dfn/`. Validate geometry against your experiment box before running DEM.

## Preview

![ZDEM DFN](docs/screenshots/preview.png)

## Install / run

```bash
git clone https://github.com/Phoenix0531-sudo/ZDEM_DFN.git
cd ZDEM_DFN
pip install -r requirements.txt
python -m zdem_dfn --help  # if console entry configured
pytest tests/
```

Pairs with Model Editor (manual structure) and ParticleTracker (post-run geometry).

## License

MIT. See [LICENSE](LICENSE).
