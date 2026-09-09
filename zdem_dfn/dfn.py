"""离散裂隙网络（DFN）随机生成：多组系、对数正态长度、截断交接。"""

import math
import random
from typing import cast

from tqdm import tqdm

from zdem_dfn.config import FRACTURE_SETS
from zdem_dfn.geometry import clip_line_segment, get_segment_intersection


def generate_dfn_network(area: float, min_x: float, max_x: float, min_y: float, max_y: float,
                         avg_diameter: float) -> tuple[list[tuple[tuple[float, float], tuple[float, float]]], int]:
    master_fractures: list[tuple[tuple[float, float], tuple[float, float]]] = []

    center_x: float = (min_x + max_x) / 2.0
    center_y: float = (min_y + max_y) / 2.0
    width: float = max_x - min_x
    height: float = max_y - min_y
    circumcircle_radius: float = math.hypot(width / 2.0, height / 2.0)

    for fset in FRACTURE_SETS:
        # 使用强类型转换消灭 IDE 冲突
        p21: float = cast(float, fset["p21"])
        length_mult: float = cast(float, fset["length_mult"])
        length_std_ratio: float = cast(float, fset.get("length_std_ratio", 0.2))
        dip_mean: float = cast(float, fset["dip_mean"])
        dip_std: float = cast(float, fset["dip_std"])
        trunc_prob: float = cast(float, fset.get("truncation_prob", 0.0))

        target_total_length: float = area * p21
        avg_length: float = avg_diameter * length_mult
        std_length: float = avg_length * length_std_ratio

        variance: float = std_length ** 2
        mu: float = math.log(avg_length ** 2 / math.sqrt(variance + avg_length ** 2))
        sigma: float = math.sqrt(math.log(1.0 + variance / (avg_length ** 2)))

        current_total_length: float = 0.0

        with tqdm(total=target_total_length, desc=f"生成组系 [{fset['set_name']}]", unit="m", leave=True) as pbar:
            while current_total_length < target_total_length:
                L: float = random.lognormvariate(mu, sigma)
                angle_deg: float = random.gauss(dip_mean, dip_std)
                angle_rad: float = math.radians(angle_deg)

                r_rand: float = circumcircle_radius * math.sqrt(random.uniform(0.0, 1.0))
                theta_rand: float = random.uniform(0.0, 2.0 * math.pi)
                cx: float = center_x + r_rand * math.cos(theta_rand)
                cy: float = center_y + r_rand * math.sin(theta_rand)

                dx: float = (L / 2.0) * math.cos(angle_rad)
                dy: float = (L / 2.0) * math.sin(angle_rad)
                curr_p1: tuple[float, float] = (cx - dx, cy - dy)
                curr_p2: tuple[float, float] = (cx + dx, cy + dy)

                if trunc_prob > 0.0 and len(master_fractures) > 0:
                    for prev_f in master_fractures:
                        intersect = get_segment_intersection(curr_p1, curr_p2, prev_f[0], prev_f[1])
                        if intersect is not None:
                            if random.random() < trunc_prob:
                                d1: float = math.hypot(curr_p1[0] - intersect[0], curr_p1[1] - intersect[1])
                                d2: float = math.hypot(curr_p2[0] - intersect[0], curr_p2[1] - intersect[1])
                                if d1 > d2:
                                    curr_p2 = intersect
                                else:
                                    curr_p1 = intersect

                clip_result = clip_line_segment(curr_p1[0], curr_p1[1], curr_p2[0], curr_p2[1], min_x, max_x, min_y, max_y)
                if clip_result is not None:
                    cx1, cy1, cx2, cy2 = clip_result
                    effective_length: float = math.hypot(cx2 - cx1, cy2 - cy1)
                    if effective_length > 0.0:
                        master_fractures.append(((cx1, cy1), (cx2, cy2)))
                        current_total_length += effective_length
                        pbar.update(effective_length)

    return master_fractures, len(master_fractures)
