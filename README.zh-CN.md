# ZDEM DFN

**面向 ZDEM 工作流的离散裂隙网络（DFN）生成辅助。**

[English](README.md) | [中文](README.zh-CN.md)

[![CI](https://github.com/Phoenix0531-sudo/ZDEM_DFN/actions/workflows/ci.yml/badge.svg)](https://github.com/Phoenix0531-sudo/ZDEM_DFN/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

面向 ZDEM 工作流的离散裂隙网络（DFN）生成辅助。

生成可喂给 DEM 模型的裂隙集合。


## 功能

- 🪓 `zdem_dfn/` 下 DFN 生成辅助
- 🔌 面向 ZDEM 的导出约定
- ✅ CI + 测试

## 快速开始

### 安装

```bash
git clone https://github.com/Phoenix0531-sudo/ZDEM_DFN.git
cd ZDEM_DFN
pip install -r requirements.txt
```

### 使用

```bash
python -m zdem_dfn --help  # 若有入口
pytest tests/
```

## 项目结构

```
zdem_dfn/
tests/  docs/
```

## 相关 ZDEM 工具

| 仓库 | 作用 |
|------|------|
| [ZDEM_ParticleTracker](https://github.com/Phoenix0531-sudo/ZDEM_ParticleTracker) | 交互颗粒追踪 + VisPy 真实半径渲染 |
| [ZDEM_Salt_Kinematics](https://github.com/Phoenix0531-sudo/ZDEM_Salt_Kinematics) | 盐构造几何 / 运动学提取与出图 |
| [ZDEM_Area_Conservation](https://github.com/Phoenix0531-sudo/ZDEM_Area_Conservation) | 面积守恒 / 三角剖分分析 |
| [ZDEM_Bond_Fracture](https://github.com/Phoenix0531-sudo/ZDEM_Bond_Fracture) | 粘结损伤序列 + 桌面 / CLI |
| [ZDEM_Damage_Thresholds](https://github.com/Phoenix0531-sudo/ZDEM_Damage_Thresholds) | 损伤阈值与应变能图 |
| [ZDEM_DFN](https://github.com/Phoenix0531-sudo/ZDEM_DFN) | ZDEM 离散裂隙网络生成 |
| [ZDEM_Model_Editor](https://github.com/Phoenix0531-sudo/ZDEM_Model_Editor) | 模型文件可视化编辑 |
| [ZDEM_Archiver](https://github.com/Phoenix0531-sudo/ZDEM_Archiver) | 大体积模拟结果归档 / 清理 |
| [ZDEM3D_WEB](https://github.com/Phoenix0531-sudo/ZDEM3D_WEB) | CAE 云端界面（Django + React + VTK.js） |

## 说明

生成工具 — 请按模型几何约束自行校验。

## 许可证

MIT。在注明出处的前提下可商业使用（以 LICENSE 为准）。详见 [LICENSE](LICENSE)。
