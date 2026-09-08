# ZDEM DFN

**面向 ZDEM 工作流的离散裂隙网络（DFN）生成。**

[English](README.md) | [中文](README.zh-CN.md)

[![CI](https://github.com/Phoenix0531-sudo/ZDEM_DFN/actions/workflows/ci.yml/badge.svg)](https://github.com/Phoenix0531-sudo/ZDEM_DFN/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

包在 `zdem_dfn/`。生成后按实验盒子几何自行校验，再导入 DEM。

```bash
pip install -r requirements.txt

# 1. 编辑 zdem_dfn/engine.py 顶部的 TARGET_DIRECTORIES / SOURCE_FILENAME，
#    指向各自包含 ZDEM 颗粒文件（ini_xyr.dat）的文件夹。
# 2. 就地批处理所有文件夹并输出预览图：
python -m zdem_dfn

pytest tests/
```

引擎读取各目标文件夹的 `ini_xyr.dat`（初始颗粒坐标），生成裂隙网络后
就地覆写该文件，并在当前目录落地 `dfn_preview.png`。默认
`TARGET_DIRECTORIES` 指向作者本机样品目录——运行前请先修改。

## 许可证

MIT。详见 [LICENSE](LICENSE)。
