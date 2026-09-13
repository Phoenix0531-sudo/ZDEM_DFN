"""预览图渲染：颗粒分组着色 + 裂隙线段 + 学术级坐标轴。"""

# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
import os
from typing import cast

from zdem_dfn.config import ParticleValue


def generate_preview_plot(lines_data: list[dict[str, ParticleValue]],
                          fractures: list[tuple[tuple[float, float], tuple[float, float]]],
                          min_x: float, max_x: float, min_y: float, max_y: float,
                          out_path: str | None = None):
    """渲染预览图。

    out_path 为 None 时保持旧行为：写入当前工作目录的 dfn_preview.png。
    """
    # 延迟导入：让 CLI --help / --dry-run 不必拉起 matplotlib 全家桶
    import matplotlib.collections as mcoll
    import matplotlib.lines as mlines
    import matplotlib.pyplot as plt
    from matplotlib.collections import PatchCollection
    from matplotlib.patches import Circle

    from zdem_dfn import config as _config

    print("[*] 正在向渲染核心移交可视化图层准备生成预览图...")
    fig, ax = plt.subplots(figsize=(5, 10), dpi=300)

    plot_dict: dict[str, list[Circle]] = {
        "Background": [],
        "DFN_Matrix": [],
        "DFN_Asperity": [],
        "DFN_Gouge": [],
        "DFN_Node": []
    }

    for obj in lines_data:
        if obj.get("type") == "particle":
            tag = cast(str, obj.get("tag")) if obj.get("tag") is not None else None

            val_x: float = cast(float, obj["x"])
            val_y: float = cast(float, obj["y"])
            val_r: float = cast(float, obj["r"])

            circle = Circle((val_x, val_y), val_r)

            if tag is None:
                plot_dict["Background"].append(circle)
            else:
                if tag in plot_dict:
                    plot_dict[tag].append(circle)

    colors_map = {
        "Background": '#E0E0E0',
        "DFN_Matrix": '#A6C4D9',
        "DFN_Asperity": '#32CD32',
        "DFN_Gouge": '#DC143C',
        "DFN_Node": '#000000'
    }

    zorders = {
        "Background": 1,
        "DFN_Matrix": 2,
        "DFN_Asperity": 3,
        "DFN_Gouge": 4,
        "DFN_Node": 5
    }

    for key, items in plot_dict.items():
        if items:
            collection = PatchCollection(items, facecolor=colors_map[key], edgecolor='#A0A0A0', linewidth=0.25, zorder=zorders[key], label=key)
            ax.add_collection(collection)

    if fractures:
        segments: list[list[tuple[float, float]]] = []
        for ((cx1, cy1), (cx2, cy2)) in fractures:
            segments.append([(cx1, cy1), (cx2, cy2)])
        lc = mcoll.LineCollection(segments, colors='#8B0000', linewidths=0.8, zorder=6)
        ax.add_collection(lc)

    ax.set_aspect('equal')
    # 视野裁剪常量始终从 config 模块读取，支持运行时覆盖
    ax.set_xlim(_config.CROP_MIN_X, _config.CROP_MAX_X)
    ax.set_ylim(_config.CROP_MIN_Y, _config.CROP_MAX_Y)

    # 刻度随 CROP 窗口动态生成（旧版硬编码 3000..6000 在窗口被覆盖时会悬空）
    n_x = 4 if (max_x - min_x) >= 1000 else 3
    n_y = 8 if (max_y - min_y) >= 8000 else 3
    if min_x != max_x:
        ax.set_xticks([min_x + i * (max_x - min_x) / n_x for i in range(n_x + 1)])
    if min_y != max_y:
        ax.set_yticks([min_y + i * (max_y - min_y) / n_y for i in range(n_y + 1)])

    ax.set_xlabel('X (m)', fontsize=12, fontweight='normal')
    ax.set_ylabel('Y (m)', fontsize=12, fontweight='normal')
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)
    ax.tick_params(axis='both', which='major', direction='in', length=6, width=1.5, labelsize=12, top=True, right=True)

    legend_elements = []
    for key in ["Background", "DFN_Matrix", "DFN_Asperity", "DFN_Gouge", "DFN_Node"]:
        if plot_dict.get(key):
            legend_elements.append(mlines.Line2D([], [], color=colors_map[key], marker='o', linestyle='None', markersize=10, label=key))

    ax.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=12, frameon=False)

    out_img = out_path if out_path is not None else os.path.join(os.getcwd(), "dfn_preview.png")
    plt.savefig(out_img, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"    - 高品质演示汇报图像已落地：{out_img}")
