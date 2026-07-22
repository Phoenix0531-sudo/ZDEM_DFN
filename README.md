<div align="center">

# ZDEM DFN · 离散裂隙网络生成引擎

**Discrete Fracture Network generation engine for ZDEM simulations**

[English](README.md) | [中文](README.zh-CN.md)

![CI](https://github.com/Phoenix0531-sudo/ZDEM_DFN/actions/workflows/ci.yml/badge.svg)

**Discrete Fracture Network Generation Engine for ZDEM Simulations**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](zdem_dfn/engine.py)
[![Dependencies](https://img.shields.io/badge/deps-tqdm%20%7C%20matplotlib-lightgrey)](requirements.txt)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)](https://github.com/Phoenix0531-sudo/ZDEM_DFN)

</div>

---

## 项目简介 | Overview

在 ZDEM 离散元数值模拟中，离散裂隙网络（DFN）的生成质量直接影响岩体力学行为的刻画精度。传统方法往往只支持单一组系产状，且缺乏对裂隙‑颗粒交互区域的细粒度分类标记。

ZDEM DFN 是一款为 ZDEM 前处理场景设计的多组系 DFN 生成引擎。它支持对数正态长度分布与高斯产状倾角的多组系裂隙生长、T/X 型交切网络的拓扑构建、基于哈希网格的空间加速索引，以及颗粒级别的地质属性标记（基质/粗糙面/断层泥/节点），最终输出可视化的预览图像。

> In ZDEM numerical simulations, the quality of Discrete Fracture Network (DFN) generation directly impacts the accuracy of rock mechanical behavior characterization. Conventional approaches often support only a single fracture set and lack fine-grained classification of fracture-particle interaction zones.
>
> **ZDEM DFN** is a multi-set DFN generation engine designed for ZDEM preprocessing. It features lognormal length distribution and Gaussian dip angle for multi-set fracture growth, T/X junction topology, hash-grid spatial acceleration indexing, and particle-level geological tagging (matrix / asperity / gouge / node), with preview visualization output.

---

## 技术特性 | Technical Highlights

| 特性 | Feature | 说明 |
|------|---------|------|
| **多组系并行生成** | Multi-set Fracture Generation | 支持主断层 + 次生微裂隙等多组系独立参数配置，每组独立控制 P21、长度、倾角分布 |
| **对数正态‑高斯耦合** | Lognormal-Gaussian Coupling | 长度服从对数正态分布，倾角服从高斯分布，贴合天然裂隙统计特征 |
| **T/X 型交切网络** | T/X Junction Network | 基于线段求交算法检测裂隙间交切关系，支持截断概率参数控制 T 型分支比率 |
| **哈希网格空间索引** | Hash-grid Spatial Indexing | 颗粒‑裂隙碰撞检测采用均匀网格空间分区，避免 O(N*M) 暴力遍历 |
| **Cohen-Sutherland 裁剪** | Cohen-Sutherland Clipping | 标准计算机图形学线段裁剪算法，确保裂隙严格限定在工作区域内部 |
| **四类地质属性标记** | 4-class Geological Tagging | 遍历颗粒自动标记为 Background / Matrix / Asperity / Gouge / Node |
| **学术级可视化** | Publication-grade Visualization | 300 DPI 矢量风格输出，支持图例、刻度内嵌、色彩区分的颗粒‑裂隙双图层 |

---

## 目录 | Table of Contents

- [数据准备 / Data Preparation](#数据准备--data-preparation)
- [算法原理 / Algorithm](#算法原理--algorithm)
- [模块文档 / Module Reference](#模块文档--module-reference)
- [快速开始 / Quick Start](#快速开始--quick-start)
- [输出说明 / Output](#输出说明--output)
- [安装依赖 / Installation](#安装依赖--installation)
- [项目结构 / Project Structure](#项目结构--project-structure)
- [引用 / Citation](#引用--citation)
- [许可证 / License](#许可证--license)

---

## 数据准备 | Data Preparation

在执行 DFN 生成之前，用户需要准备以下数据：

1. **ini_xyr.dat 文件**：每个围压容器目录下存放一个 `ini_xyr.dat`，每行包含 `X Y R` 三列数据，分别代表颗粒的 x 坐标、y 坐标和半径。支持科学计数法格式。
2. **目录结构**：在脚本的 `TARGET_DIRECTORIES` 列表中配置所有待处理的围压矩阵路径，引擎会以第一个目录中的文件作为参照系提取全场几何参数。
3. **裁剪区域**：通过 `CROP_MIN_X` / `CROP_MAX_X` / `CROP_MIN_Y` / `CROP_MAX_Y` 定义核心工作区边界。

> Before running the DFN generation, prepare the following:
>
> 1. **ini_xyr.dat files**: place one `ini_xyr.dat` per confining-pressure directory, each line containing `X Y R` columns (x-coordinate, y-coordinate, radius). Scientific notation is supported.
> 2. **Directory layout**: configure all target paths in `TARGET_DIRECTORIES`. The first directory serves as reference for extracting global geometric parameters.
> 3. **Crop region**: define the core working area via `CROP_MIN_X` / `CROP_MAX_X` / `CROP_MIN_Y` / `CROP_MAX_Y`.

---

## 算法原理 | Algorithm

### 1. 多组系裂隙生长 | Multi-set Fracture Growth

每组裂隙由 `FRACTURE_SETS` 中的字典参数控制：

| 参数 | Parameter | 作用 |
|------|-----------|------|
| P21 | P21 (m/m^2) | 目标裂隙密度（单位面积总长度），决定生成条数 |
| length_mult | Length multiplier | 以颗粒平均直径为基准的裂隙长度乘数 |
| length_std_ratio | Length std ratio | 长度标准差与均值之比，控制对数正态分布的形状 |
| dip_mean / dip_std | Dip mean / std | 倾角均值与标准差，高斯采样产状方向 |
| truncation_prob | Truncation prob | 遇见已有裂隙时被截断的概率，控制 T 型交接比率 |

### 2. 哈希网格碰撞检测 | Hash-grid Collision Detection

将工作区划分为均匀网格，每个颗粒按网格坐标存入哈希表。遍历裂隙时仅查询裂隙包围盒所覆盖的网格单元，将时间复杂度从 O(N\*M) 降至 O(N + M\*k)，其中 k 为每个裂隙的平均邻近颗粒数。

### 3. T/X 网络拓扑 | T/X Junction Topology

采用标准线段求交算法判断两条线段是否相交。当新裂隙与已有裂隙相交，根据 `truncation_prob` 截断当前裂隙的远端，形成 T 型分支而非 X 型贯通。

### 4. 颗粒标记策略 | Particle Tagging Strategy

颗粒与裂隙的距离 ≤ 颗粒半径时视为被切中。根据切中次数和开关配置（`ENABLE_HETEROGENEOUS` / `ENABLE_NODE_PENALTY`）赋予不同的地质标签：

| 标签 | Tag | 条件 |
|------|-----|------|
| DFN_Matrix | 基质 | 默认被切中标记（概率 60%） |
| DFN_Asperity | 粗糙面 | 仅启用非均质时随机分配（概率 15%） |
| DFN_Gouge | 断层泥 | 仅启用非均质时随机分配（概率 25%） |
| DFN_Node | 节点 | 启用节点惩罚且被 2+ 条裂隙切中 |

> The core algorithm pipeline proceeds as:
>
> 1. **Multi-set Fracture Growth**: each set samples lengths from a lognormal distribution and dip angles from a Gaussian distribution, placing fractures uniformly within the circumscribed circle of the working area.
> 2. **Cohen-Sutherland Clipping**: each fracture segment is clipped against the rectangular crop boundary to ensure strict containment.
> 3. **T/X Junction Detection**: segment intersection detection runs between new and existing fractures. T-junctions form when `truncation_prob` triggers.
> 4. **Hash-grid Spatial Indexing**: particles are binned into a uniform grid. Fracture-particle intersection checks only visit grid cells overlapped by each fracture's bounding box.
> 5. **Tag Assignment**: intersected particles receive geological tags (Matrix / Asperity / Gouge / Node) based on configuration flags and random sampling.

---

## 模块文档 | Module Reference

### 全局控制参数 | Global Control Parameters

| 参数 | Parameter | 类型 | 默认值 | 说明 |
|------|-----------|------|--------|------|
| `CROP_MIN_X` | Crop min X | float | 2000.0 | 核心区 X 下限 |
| `CROP_MAX_X` | Crop max X | float | 6000.0 | 核心区 X 上限 |
| `CROP_MIN_Y` | Crop min Y | float | 3000.0 | 核心区 Y 下限 |
| `CROP_MAX_Y` | Crop max Y | float | 11000.0 | 核心区 Y 上限 |
| `ENABLE_HETEROGENEOUS` | Heterogeneous flag | bool | False | 启用非均质随机标记 |
| `ENABLE_NODE_PENALTY` | Node penalty flag | bool | False | 启用节点（2+ 裂隙交切）标记 |
| `SOURCE_FILENAME` | Source filename | str | ini_xyr.dat | 输入文件名 |
| `TARGET_FILENAME` | Target filename | str | ini_xyr.dat | 输出文件名 |

### 组系参数 | Fracture Set Parameters

| 参数 | Parameter | 类型 | 说明 |
|------|-----------|------|------|
| `set_name` | Set name | str | 组系名称（仅用于控制台显示） |
| `p21` | P21 density | float | 目标裂隙密度 (m/m^2) |
| `length_mult` | Length multiplier | float | 裂隙长度与颗粒平均直径之比 |
| `length_std_ratio` | Length std ratio | float | 长度对数正态分布的形状参数 |
| `dip_mean` | Dip mean | float | 倾角均值 (度) |
| `dip_std` | Dip std | float | 倾角标准差 (度) |
| `truncation_prob` | Truncation prob | float | 0~1，被已有裂隙截断的概率 |

### 核心函数 | Core Functions

| 函数 | Function | 说明 |
|------|----------|------|
| `generate_dfn_network()` | Generate DFN network | 多组系裂隙网络主生成函数，返回裂隙列表与数量 |
| `clip_line_segment()` | Clip line segment | Cohen-Sutherland 线段裁剪，确保裂隙在工作区内 |
| `get_segment_intersection()` | Segment intersection | 两线段求交，返回交点坐标或 None |
| `point_to_segment_distance()` | Point-segment distance | 点到线段的最短距离 |
| `output_tagged_coordinates()` | Output tagged file | 将标记结果写回 ini_xyr.dat（追加 tag 列） |
| `generate_preview_plot()` | Generate preview plot | 输出 300 DPI 预览图 dfn_preview.png |

---

## 快速开始 | Quick Start

### 方式一：直接运行 | Run Directly

```bash
# 编辑 zdem_dfn/engine.py 中的 TARGET_DIRECTORIES 路径配置
# 然后执行
python -m zdem_dfn.engine
```

### 方式二：pip 安装后运行 | Install & Run

```bash
pip install .
zdem-dfn
```

### 方式三：开发模式 | Development Mode

```bash
pip install -e .
python -m zdem_dfn.engine
```

### 完整示例 | Complete Example

```python
from zdem_dfn.engine import generate_dfn_network

# 参数：工作区面积、边界、颗粒平均直径
area = 4000.0 * 8000.0
fractures, count = generate_dfn_network(
    area=area,
    min_x=2000.0, max_x=6000.0,
    min_y=3000.0, max_y=11000.0,
    avg_diameter=0.05
)
print(f"Generated {count} fractures")
```

---

## 输出说明 | Output

### 控制台输出 | Console Output

引擎在运行过程中输出四个阶段的进度信息：

```
============================================================
 ZDEM 高级离散元就地解析前处理 - 混合多组系 T/X 网络双边引擎
============================================================
[*] 【全局一阶段】 正在从主坐标系汲取宏观基底场信息...
[*] 源文件真实检测区域 => X: 1980.320~6020.150, Y: 2980.460~11010.330
[*] 【全局二阶段】 生成全局唯一确定的几何骨架 (Fracture Set)...
生成组系 [Primary_Fault]: 100%|████████| 64.0/64.0 [00:02<00:00, 28.5m/s]
生成组系 [Secondary_Joints]: 100%|████████| 9.60/9.60 [00:00<00:00, 31.2m/s]
[*] 【全局三阶段】 进入围岩批次循环系统就地解析...
[*] 【全局四阶段】 影像学构建收尾...
============================================================
  ● 地壳破碎再造引擎，批调解析历时总计: 3.472 秒
============================================================
```

### 图表输出 | Figure Output

生成的 `dfn_preview.png` 包含：

- **颗粒层**：以不同颜色区分 Background（灰色）、DFN_Matrix（蓝色）、DFN_Asperity（绿色）、DFN_Gouge（红色）、DFN_Node（黑色）
- **裂隙层**：深红色线段叠加在颗粒之上
- **坐标轴**：学术级刻度内嵌风格，单位米（m）
- **图例**：置于图像右侧，标注每类颗粒和裂隙

### 数据文件输出 | Data File Output

每个目标目录下的 `ini_xyr.dat` 被覆写为带 tag 列的新文件：

```
1.234567890123e+03  4.567890123456e+03  2.345678901234e-02
1.345678901234e+03  4.678901234567e+03  1.234567890123e-02  DFN_Matrix
```

其中被裂隙切中的颗粒在原数据后追加 Tab 分隔的标签字符串，未被切中的颗粒保持三列纯净格式。

> The engine produces three outputs:
>
> 1. **Console log** with 4-phase progress indicators and tqdm bars per fracture set.
> 2. **Preview figure** `dfn_preview.png` at 300 DPI with color-coded particles and fracture overlay.
> 3. **Tagged data files** overwriting each `ini_xyr.dat` with appended geological tags.

---

## 安装依赖 | Installation

### 依赖列表 | Dependencies

| 包 | Package | 最低版本 | 用途 |
|---|---------|----------|------|
| tqdm | tqdm | 4.62.0 | 进度条显示 |
| matplotlib | matplotlib | 3.4.0 | 可视化与图像输出 |

### 安装命令 | Commands

```bash
# 安装运行时依赖
pip install -r requirements.txt

# 完整安装（推荐）
pip install -e .
```

> Python 3.10 or later is required due to the use of `str | float` union type syntax.

---

## 项目结构 | Project Structure

```
ZDEM_DFN/
├── zdem_dfn/
│   ├── __init__.py      # 包初始化，版本与许可证信息
│   └── engine.py        # DFN 生成引擎核心模块
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── setup.py
```

---

## 引用 | Citation

If you use ZDEM DFN in your research, please cite it as:

```bibtex
@software{zdem_dfn2026,
  title     = {{ZDEM DFN}: Discrete Fracture Network Generation Engine for ZDEM Simulations},
  year      = {2026},
  url       = {https://github.com/Phoenix0531-sudo/ZDEM_DFN},
  version   = {1.0.0},
  license   = {MIT}
}
```

---

## ZDEM Tool Family

Related open-source tools in the same ZDEM / DEM workflow (same author):

| Repo | Role |
|------|------|
| [ZDEM_ParticleTracker](https://github.com/Phoenix0531-sudo/ZDEM_ParticleTracker) | VisPy particle tracking desktop app (true-radius discs, permanent IDs) |
| [ZDEM_Archiver](https://github.com/Phoenix0531-sudo/ZDEM_Archiver) | Safe purge of timestep dumps while keeping reproducible sources |
| [ZDEM_Area_Conservation](https://github.com/Phoenix0531-sudo/ZDEM_Area_Conservation) | Delaunay coverage area vs load step |
| [ZDEM_Bond_Fracture](https://github.com/Phoenix0531-sudo/ZDEM_Bond_Fracture) | Bond damage / fracture time series + ROI |
| [ZDEM_Damage_Thresholds](https://github.com/Phoenix0531-sudo/ZDEM_Damage_Thresholds) | Damage evolution and crack thresholds |
| [ZDEM_DFN](https://github.com/Phoenix0531-sudo/ZDEM_DFN) | Discrete fracture network generation |
| [ZDEM_Model_Editor](https://github.com/Phoenix0531-sudo/ZDEM_Model_Editor) | tkinter + matplotlib model file editor |
| [ZDEM_Salt_Kinematics](https://github.com/Phoenix0531-sudo/ZDEM_Salt_Kinematics) | Salt kinematics automation for ZDEM outputs |
| [ZDEM3D_WEB](https://github.com/Phoenix0531-sudo/ZDEM3D_WEB) | 3D web CAE front (VTK + Django/React) |

Typical pipeline: **Model_Editor / DFN → ZDEM run → Archiver (disk) → ParticleTracker / Bond / Area / Salt / Damage (analysis)**.

## 许可证 | License

This project is open-sourced under the **MIT License**. See [LICENSE](LICENSE) for details.

---

<div align="center">

**Made for the ZDEM research community**

</div>

## License

[MIT](LICENSE) — free for commercial use with attribution.
