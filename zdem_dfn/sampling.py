"""采样与分组机制：颗粒-裂隙作用分带、网格哈希加速、随机概率机制。

所有配置开关通过 ``_config.`` 属性访问（而非 import 快照），
保证运行时覆盖 ``zdem_dfn.config`` 后立即生效。

与旧引擎的等价性：交带判定 ``dist <= r``（含等于），
``intersect_count`` 对每条命中裂隙累加（支撑节点惩罚 >=2 判定）。
"""

import math
import random
from collections import defaultdict
from typing import cast

from zdem_dfn import config as _config
from zdem_dfn.geometry import point_to_segment_distance


def build_hash_grid(lines_data, grid_cell_size: float) -> dict[tuple[int, int], list[int]]:
    """按网格单元建立颗粒索引，供近邻裂隙查询加速。"""
    hash_grid: dict[tuple[int, int], list[int]] = defaultdict(list)
    for idx, p in enumerate(lines_data):
        if p.get("type") == "particle":
            base_px: float = cast(float, p["x"])
            base_py: float = cast(float, p["y"])
            base_gx: int = int(base_px // grid_cell_size)
            base_gy: int = int(base_py // grid_cell_size)
            hash_grid[(base_gx, base_gy)].append(idx)
    return hash_grid


def apply_fracture_tagging(lines_data, fractures, grid_cell_size: float, max_r: float) -> dict[str, int]:
    """裂隙-颗粒作用与属性标记（原 main() 全局三阶段内联逻辑的函数化割离）。

    返回各标签命中统计（stat_tags）。行为与旧引擎一致：
    - 网格哈希只圈定候选颗粒，最终判定仍逐颗精确求距；
    - ``dist <= r`` 计为相交，每条命中裂隙 ``intersect_count`` 累加；
    - 节点惩罚在异质标记之前生效（>=2 次相交直接 DFN_Node）。
    """
    hash_grid = build_hash_grid(lines_data, grid_cell_size)

    for (x1, y1), (x2, y2) in fractures:
        search_min_x: float = min(x1, x2) - max_r
        search_max_x: float = max(x1, x2) + max_r
        search_min_y: float = min(y1, y2) - max_r
        search_max_y: float = max(y1, y2) + max_r

        sgx: int = int(search_min_x // grid_cell_size)
        egx: int = int(search_max_x // grid_cell_size)
        sgy: int = int(search_min_y // grid_cell_size)
        egy: int = int(search_max_y // grid_cell_size)

        for gx in range(sgx, egx + 1):
            for gy in range(sgy, egy + 1):
                if (gx, gy) in hash_grid:
                    for p_idx in hash_grid[(gx, gy)]:
                        target_p = lines_data[p_idx]
                        pt_x: float = cast(float, target_p["x"])
                        pt_y: float = cast(float, target_p["y"])
                        pt_r: float = cast(float, target_p["r"])
                        dist: float = point_to_segment_distance(pt_x, pt_y, x1, y1, x2, y2)
                        if dist <= pt_r:
                            target_p["intersect_count"] = cast(int, target_p.get("intersect_count", 0)) + 1

    stat_tags: dict[str, int] = {
        'DFN_Node': 0, 'DFN_Asperity': 0, 'DFN_Matrix': 0, 'DFN_Gouge': 0
    }

    for p in lines_data:
        if p.get("type") == "particle":
            intersect_cnt: int = cast(int, p.get("intersect_count", 0))
            if intersect_cnt > 0:
                tag: str | None = None
                if _config.ENABLE_NODE_PENALTY and intersect_cnt >= 2:
                    tag = "DFN_Node"
                else:
                    if _config.ENABLE_HETEROGENEOUS:
                        rand_val: float = random.random()
                        if rand_val < _config.PROB_ASPERITY:
                            tag = "DFN_Asperity"
                        elif rand_val < _config.PROB_ASPERITY + _config.PROB_MATRIX:
                            tag = "DFN_Matrix"
                        else:
                            tag = "DFN_Gouge"
                    else:
                        tag = "DFN_Matrix"
                p["tag"] = tag
                if tag is not None:
                    stat_tags[tag] = stat_tags.get(tag, 0) + 1

    return stat_tags


def process_single_folder_lines(dfn_segments, lines_data):
    """兼容别名（无网格加速）：等价于 grid_cell_size 视作无限大的退化情形。"""
    for obj in lines_data:
        if obj.get("type") == "particle":
            val_x: float = cast(float, obj["x"])
            val_y: float = cast(float, obj["y"])
            val_r: float = cast(float, obj["r"])
            for seg_p1, seg_p2 in dfn_segments:
                dist = point_to_segment_distance(val_x, val_y, seg_p1[0], seg_p1[1], seg_p2[0], seg_p2[1])
                if dist <= val_r:
                    obj["intersect_count"] = cast(int, obj.get("intersect_count", 0)) + 1
            if cast(int, obj.get("intersect_count", 0)) > 0:
                obj["tag"] = random_tag_by_probability()


def check_particles_overlap(x1: float, y1: float, r1: float, x2: float, y2: float, r2: float,
                            min_gap: float = 0.0) -> bool:
    """两颗粒是否重叠（可选最小间隙）。"""
    center_dist: float = math.hypot(x2 - x1, y2 - y1)
    return center_dist < (r1 + r2 + min_gap)


def random_tag_by_probability() -> str:
    """按概率矩阵返回标签（异质模式关闭时统一 DFN_Matrix，不含节点惩罚）。"""
    if not _config.ENABLE_HETEROGENEOUS:
        return "DFN_Matrix"
    roll: float = random.random()
    if roll < _config.PROB_ASPERITY:
        return "DFN_Asperity"
    elif roll < _config.PROB_ASPERITY + _config.PROB_MATRIX:
        return "DFN_Matrix"
    else:
        return "DFN_Gouge"
