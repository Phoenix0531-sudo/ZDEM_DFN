# ZDEM DFN

**面向 ZDEM 颗粒包的离散裂隙网络生成器**

[English](README.md) | [中文](README.zh-CN.md)

![CI](https://github.com/Phoenix0531-sudo/ZDEM_DFN/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

ZDEM DFN 在 ZDEM 风格的颗粒初始包（`ini_xyr.dat`）上生成**离散裂隙网络**，用于岩石力学 / DEM 前处理。

核心为 `zdem_dfn/engine.py`：多组系裂隙、可选非均质模式、matplotlib 诊断。安装后控制台命令：`zdem-dfn`。

## 为什么做这个

每个实验目录手搓 DFN 无法扩展。本包装中参数与批量目标，服务 ZDEM 工作流。

## 功能

- 读写 ZDEM 向的初始颗粒文件  
- 多组系裂隙（长度 / 方位统计）  
- 生成区域裁剪窗口  
- `tqdm` 进度；可选预览图  
- 可安装入口 `zdem-dfn`  

## 安装

```bash
git clone https://github.com/Phoenix0531-sudo/ZDEM_DFN.git
cd ZDEM_DFN
pip install -r requirements.txt
pip install -e .
```

## 使用

1. 在 `zdem_dfn/engine.py` 中配置 `TARGET_DIRECTORIES` / 源文件名（或写小驱动调用引擎）。  
2. 运行：

```bash
zdem-dfn
# 或
python -m zdem_dfn.engine
```

输入一般为 `ini_xyr.dat`；按模型域调整 `CROP_MIN_X` 等裁剪范围。

## 目录结构

```
zdem_dfn/engine.py
setup.py
tests/
```

## 相关 ZDEM 工具

| 仓库 | 作用 |
|------|------|
| [ZDEM_ParticleTracker](https://github.com/Phoenix0531-sudo/ZDEM_ParticleTracker) | 交互式颗粒追踪 + VisPy 真实半径渲染 |
| [ZDEM_Salt_Kinematics](https://github.com/Phoenix0531-sudo/ZDEM_Salt_Kinematics) | 盐体几何/运动学提取与出图 |
| [ZDEM_Area_Conservation](https://github.com/Phoenix0531-sudo/ZDEM_Area_Conservation) | 面积守恒 / 三角网格分析 |
| [ZDEM_Bond_Fracture](https://github.com/Phoenix0531-sudo/ZDEM_Bond_Fracture) | 粘结损伤序列 + 桌面/CLI |
| [ZDEM_Damage_Thresholds](https://github.com/Phoenix0531-sudo/ZDEM_Damage_Thresholds) | 损伤阈值与应变–能量图 |
| [ZDEM_DFN](https://github.com/Phoenix0531-sudo/ZDEM_DFN) | ZDEM 离散裂隙网络生成 |
| [ZDEM_Model_Editor](https://github.com/Phoenix0531-sudo/ZDEM_Model_Editor) | 模型文件可视化编辑 |
| [ZDEM_Archiver](https://github.com/Phoenix0531-sudo/ZDEM_Archiver) | 大体量模拟结果归档清理 |
| [ZDEM3D_WEB](https://github.com/Phoenix0531-sudo/ZDEM3D_WEB) | CAE 云端界面（Django + React + VTK.js） |
## 许可证

MIT。可在署名前提下商用。见 [LICENSE](LICENSE)。
