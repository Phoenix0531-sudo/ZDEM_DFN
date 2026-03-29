# pyright: reportMissingImports=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportAny=false
import os
import math
import random
import time
from collections import defaultdict
from typing import cast

import matplotlib.pyplot as plt  # type: ignore
import matplotlib.collections as mcoll  # type: ignore

# ==========================================
# 模块 1：全局控制开关与宏观参数配置区
# ==========================================
INPUT_FILE = "E:/0.Information/4.Temp/StructLab/岩石力学/DFN/0.GEN/ini_xyr.dat"           
OUTPUT_FILE = "E:/0.Information/4.Temp/StructLab/岩石力学/DFN/0.GEN/dfn_ini_xyr.dat"

# 机制总控开关
ENABLE_HETEROGENEOUS = False          
ENABLE_NODE_PENALTY = True           

# 强类型别名使用最新 Python 3.10+ 原生语法 |
FractureValue = str | float
ParticleValue = str | float | int | None

# -------------------------------------------------------------------
# 新特性 2：多组系控制台 (Multiple Fracture Sets)
# -------------------------------------------------------------------
FRACTURE_SETS: list[dict[str, FractureValue]] = [
    {
        "set_name": "Primary_Fault",
        "p21": 0.06,                 
        "length_mult": 12.0,         
        "length_std_ratio": 0.2,     
        "dip_mean": 45.0,            
        "dip_std": 2.0,              
        "truncation_prob": 0.0       
    },
    {
        "set_name": "Secondary_Joints",
        "p21": 0.04,
        "length_mult": 6.0,
        "length_std_ratio": 0.2,
        "dip_mean": -45.0,
        "dip_std": 5.0,
        "truncation_prob": 0.85      
    }
]

PROB_ASPERITY = 0.15                 
PROB_MATRIX = 0.60                   
PROB_GOUGE = 0.25                    

def point_to_segment_distance(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    dx: float = x2 - x1
    dy: float = y2 - y1
    L2: float = dx * dx + dy * dy
    if L2 == 0.0:
        return math.hypot(px - x1, py - y1)
    
    t: float = ((px - x1) * dx + (py - y1) * dy) / L2
    t = max(0.0, min(1.0, t))
    proj_x: float = x1 + t * dx
    proj_y: float = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)

INSIDE = 0  
LEFT = 1    
RIGHT = 2   
BOTTOM = 4  
TOP = 8     

def _compute_outcode(x: float, y: float, min_x: float, max_x: float, min_y: float, max_y: float) -> int:
    code: int = INSIDE
    if x < min_x:
        code |= LEFT
    elif x > max_x:
        code |= RIGHT
    if y < min_y:
        code |= BOTTOM
    elif y > max_y:
        code |= TOP
    return code

def clip_line_segment(x1: float, y1: float, x2: float, y2: float, min_x: float, max_x: float, min_y: float, max_y: float) -> tuple[float, float, float, float] | None:
    outcode1: int = _compute_outcode(x1, y1, min_x, max_x, min_y, max_y)
    outcode2: int = _compute_outcode(x2, y2, min_x, max_x, min_y, max_y)
    accept: bool = False

    while True:
        if not (outcode1 | outcode2):
            accept = True
            break
        elif outcode1 & outcode2:
            break
        else:
            outcode_out: int = outcode1 if outcode1 else outcode2
            x: float = 0.0
            y: float = 0.0

            if outcode_out & TOP:
                x = x1 + (x2 - x1) * (max_y - y1) / (y2 - y1)
                y = max_y
            elif outcode_out & BOTTOM:
                x = x1 + (x2 - x1) * (min_y - y1) / (y2 - y1)
                y = min_y
            elif outcode_out & RIGHT:
                y = y1 + (y2 - y1) * (max_x - x1) / (x2 - x1)
                x = max_x
            elif outcode_out & LEFT:
                y = y1 + (y2 - y1) * (min_x - x1) / (x2 - x1)
                x = min_x

            if outcode_out == outcode1:
                x1, y1 = x, y
                outcode1 = _compute_outcode(x1, y1, min_x, max_x, min_y, max_y)
            else:
                x2, y2 = x, y
                outcode2 = _compute_outcode(x2, y2, min_x, max_x, min_y, max_y)
                
    if accept:
        return (x1, y1, x2, y2)
    else:
        return None

def get_segment_intersection(p1: tuple[float, float], p2: tuple[float, float], 
                             p3: tuple[float, float], p4: tuple[float, float]) -> tuple[float, float] | None:
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    
    denom: float = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-12:
        return None  
    
    t: float = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u: float = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    
    if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
        px: float = x1 + t * (x2 - x1)
        py: float = y1 + t * (y2 - y1)
        return (px, py)
    return None

def generate_dfn_network(area: float, min_x: float, max_x: float, min_y: float, max_y: float, avg_diameter: float) -> tuple[list[tuple[tuple[float, float], tuple[float, float]]], int]:
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
                    
    return master_fractures, len(master_fractures)

def output_zdem_commands(output_path: str, tags_dict: dict[str, list[int]]):
    print(f"[*] 正在极速组装 ZDEM 命令流导出序列 '{output_path}'...")
    with open(output_path, "w", encoding="utf-8") as f:
        _ = f.write(";; ==========================================\n")
        _ = f.write(";; ZDEM DFN GROUP ASSIGNMENT COMMAND STREAM\n")
        _ = f.write(";; ==========================================\n\n")
        
        for tag_name, ids_list in tags_dict.items():
            if not ids_list:
                continue
            
            _ = f.write(f";; 正在分配物理群组 '{tag_name}' (合集颗粒数: {len(ids_list)})\n")
            chunk_size = 100
            for i in range(0, len(ids_list), chunk_size):
                chunk = ids_list[i:i+chunk_size]
                ids_str = " ".join(str(x) for x in chunk)
                _ = f.write(f"group '{tag_name}' range id {ids_str}\n")
            _ = f.write("\n")
            
        _ = f.write(";; ==========================================\n")
        _ = f.write(";; MACROSCOPIC MICRO-PARAMETERS INJECTION\n")
        _ = f.write(";; ==========================================\n")
        _ = f.write("prop fric 2.5 ebmod 1.5e10 gbmod 1.5e10 tstrength 1.1e7 sstrength 2.4e7 range group ball_rand\n")
        _ = f.write("prop fric 0.5 ebmod 1.5e9 gbmod 1.5e9 tstrength 1.0e5 sstrength 2.0e5 range group DFN_Gouge\n")
        _ = f.write("prop fric 0.8 ebmod 2.5e9 gbmod 2.5e9 tstrength 3.0e5 sstrength 5.0e5 range group DFN_Matrix\n")
        _ = f.write("prop fric 3.0 ebmod 2.0e10 gbmod 2.0e10 tstrength 1.5e7 sstrength 3.0e7 range group DFN_Asperity\n")
        _ = f.write("prop fric 0.1 ebmod 5.0e8 gbmod 5.0e8 tstrength 1e4 sstrength 1e4 range group DFN_Node\n")

def generate_preview_plot(lines_data: list[dict[str, ParticleValue]], fractures: list[tuple[tuple[float, float], tuple[float, float]]], 
                          min_x: float, max_x: float, min_y: float, max_y: float):
    print("[*] 正在向渲染核心移交可视化图层准备生成预览图...")
    fig, ax = plt.subplots(figsize=(10, 10), dpi=300)  # type: ignore
    
    plot_dict: dict[str, list[list[float]]] = {
        "Background": [[], []],   
        "DFN_Matrix": [[], []],   
        "DFN_Asperity": [[], []], 
        "DFN_Gouge": [[], []],    
        "DFN_Node": [[], []]      
    }
    
    for obj in lines_data:
        if obj.get("type") == "particle":
            tag = cast(str, obj.get("tag")) if obj.get("tag") is not None else None
            
            # 使用强类型收缩，抛弃运行时类型检查函数 float() 的约束矛盾报警
            val_x: float = cast(float, obj["x"])
            val_y: float = cast(float, obj["y"])
            
            if tag is None:
                plot_dict["Background"][0].append(val_x)
                plot_dict["Background"][1].append(val_y)
            else:
                if tag in plot_dict: 
                    plot_dict[tag][0].append(val_x)
                    plot_dict[tag][1].append(val_y)
    
    if plot_dict["Background"][0]:
        ax.scatter(plot_dict["Background"][0], plot_dict["Background"][1], s=0.5, c='#E0E0E0', marker='o', label='Background', zorder=1)  # type: ignore
    if plot_dict["DFN_Matrix"][0]:
        ax.scatter(plot_dict["DFN_Matrix"][0], plot_dict["DFN_Matrix"][1], s=1.0, c='#87CEFA', marker='o', label='DFN_Matrix', zorder=2)  # type: ignore
    if plot_dict["DFN_Asperity"][0]:
        ax.scatter(plot_dict["DFN_Asperity"][0], plot_dict["DFN_Asperity"][1], s=1.0, c='#32CD32', marker='o', label='DFN_Asperity', zorder=3)  # type: ignore
    if plot_dict["DFN_Gouge"][0]:
        ax.scatter(plot_dict["DFN_Gouge"][0], plot_dict["DFN_Gouge"][1], s=1.0, c='#DC143C', marker='o', label='DFN_Gouge', zorder=4)  # type: ignore
    if plot_dict["DFN_Node"][0]:
        ax.scatter(plot_dict["DFN_Node"][0], plot_dict["DFN_Node"][1], s=3.0, c='#000000', marker='*', label='DFN_Node', zorder=5)  # type: ignore

    if fractures:
        segments: list[list[tuple[float, float]]] = []
        for ((cx1, cy1), (cx2, cy2)) in fractures:
            segments.append([(cx1, cy1), (cx2, cy2)])
        lc = mcoll.LineCollection(segments, colors='#8B0000', linewidths=0.8, zorder=6)  # type: ignore
        ax.add_collection(lc)  # type: ignore

    ax.set_aspect('equal')  # type: ignore
    ax.set_xlim(min_x, max_x)  # type: ignore
    ax.set_ylim(min_y, max_y)  # type: ignore
    ax.set_title("ZDEM Multi-Set Discrete Fracture Network Generative Module")  # type: ignore
    
    leg = ax.legend(loc='upper right', markerscale=5.0)  # type: ignore
    for lh in leg.legend_handles:  # type: ignore
        lh.set_alpha(1.0)  # type: ignore
        
    out_img = os.path.join(os.path.dirname(OUTPUT_FILE), "dfn_preview.png")
    plt.tight_layout()  # type: ignore
    plt.savefig(out_img)  # type: ignore
    plt.close(fig)  # type: ignore
    print(f"    - 高品质演示汇报图像已落地：{out_img}")

def main():
    print("="*60)
    print(" ZDEM 高级离散元生成前处理 - 混合多组系 T/X 网络引擎")
    print("="*60)
    
    start_time = time.time()
    
    if not os.path.exists(INPUT_FILE):
        print(f"[严重错误] 未能找到输入文件：{INPUT_FILE}")
        return

    print(f"[*] 正在吞吐并缓存物理颗粒基站空间文件 '{INPUT_FILE}'...")
    lines_data: list[dict[str, ParticleValue]] = []      
    min_x: float = float('inf')
    max_x: float = float('-inf')
    min_y: float = float('inf')
    max_y: float = float('-inf')
    max_r: float = 0.0          
    sum_diameter: float = 0.0
    valid_p_count: int = 0
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            raw = line.rstrip('\n')
            if not raw.strip():
                lines_data.append({"type": "empty", "raw": raw})
                continue
            
            parts = raw.split()
            if len(parts) >= 3:
                try:
                    x_val: float = float(parts[0])
                    y_val: float = float(parts[1])
                    r_val: float = float(parts[2])
                    
                    valid_p_count += 1
                    
                    lines_data.append({
                        "type": "particle", 
                        "raw": raw,
                        "p_id": valid_p_count, 
                        "x": x_val, "y": y_val, "r": r_val,
                        "intersect_count": 0,
                        "tag": None
                    })
                    
                    min_x = min(min_x, x_val)
                    max_x = max(max_x, x_val)
                    min_y = min(min_y, y_val)
                    max_y = max(max_y, y_val)
                    max_r = max(max_r, r_val)
                    sum_diameter += (2.0 * r_val)
                except ValueError:
                    lines_data.append({"type": "header", "raw": raw})
            else:
                lines_data.append({"type": "header", "raw": raw})
                
    if valid_p_count == 0:
        print("[错误] 未能从文件中解析出有效的颗粒坐标群。")
        return

    avg_diameter: float = sum_diameter / valid_p_count
    model_width: float = max_x - min_x
    model_height: float = max_y - min_y
    model_area: float = model_width * model_height

    print(f"    - 模型系统鉴定内部颗粒基量: {valid_p_count} 颗")
    print(f"    - 参数校勘整体圆球半径均标: {avg_diameter:.6f}")
    print(f"    - 面板二次元面积包围测录值: {model_area:.6f} (X: {min_x:.3f}~{max_x:.3f}, Y: {min_y:.3f}~{max_y:.3f})")

    print("\n[*] 正在由 FRACTURE SETS 内置多动力学矩阵约束下产生深渊断层体 (DFN)...")
    fractures, num_fractures = generate_dfn_network(
        model_area, min_x, max_x, min_y, max_y, avg_diameter)
    print(f"    - 数据总线历经拦截机制后确立并存活实体断裂线条数: {num_fractures} 条")

    print("\n[*] 正在针对碰撞事件搭建前途无量的哈希虚拟锚定场网格 (Hash Grid)...")
    reference_length_base: float = avg_diameter * cast(float, FRACTURE_SETS[0]["length_mult"])
    grid_cell_size: float = reference_length_base * 1.5
    hash_grid: dict[tuple[int, int], list[int]] = defaultdict(list)
    
    for idx, p in enumerate(lines_data):
        if p.get("type") == "particle":
            base_px: float = cast(float, p["x"])  
            base_py: float = cast(float, p["y"])  
            base_gx: int = int(base_px // grid_cell_size)  
            base_gy: int = int(base_py // grid_cell_size)  
            hash_grid[(base_gx, base_gy)].append(idx)
            
    print(f"    - 单元尺寸规格敲定完结: {grid_cell_size:.6f}")
    print(f"    - 全部颗粒矩阵已被捕获映射进高速容器。")

    print("\n[*] 即将发起暴力美学的几何光线投射并开展极速切分判别...")
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

    print("[*] 面向微颗粒开展多元离散强度材料印戳赋值判定系统...")
    stat_tags: dict[str, int] = {
        'DFN_Node': 0,
        'DFN_Asperity': 0,
        'DFN_Matrix': 0,
        'DFN_Gouge': 0
    }
    
    tag_id_collections: dict[str, list[int]] = {
        'DFN_Node': [],
        'DFN_Asperity': [],
        'DFN_Matrix': [],
        'DFN_Gouge': []
    }
    
    for p in lines_data:
        if p.get("type") == "particle":
            intersect_cnt: int = cast(int, p.get("intersect_count", 0)) 
            if intersect_cnt > 0:
                tag: str | None = None
                
                if ENABLE_NODE_PENALTY and intersect_cnt >= 2: 
                    tag = "DFN_Node"
                else:
                    if ENABLE_HETEROGENEOUS:
                        rand_val: float = random.random()
                        if rand_val < PROB_ASPERITY:
                            tag = "DFN_Asperity"
                        elif rand_val < PROB_ASPERITY + PROB_MATRIX:
                            tag = "DFN_Matrix"
                        else:
                            tag = "DFN_Gouge"
                    else:
                        tag = "DFN_Matrix"
                        
                p["tag"] = tag
                if tag in stat_tags:
                    stat_tags[tag] += 1
                    tag_id_collections[tag].append(cast(int, p["p_id"])) 

    output_zdem_commands(OUTPUT_FILE, tag_id_collections)
    generate_preview_plot(lines_data, fractures, min_x, max_x, min_y, max_y)

    elapsed_time = time.time() - start_time
    
    print("\n" + "="*60)
    print(" 生成统计汇总报告")
    print("="*60)
    print(f"  ● 高度断裂交叉集射点 (DFN_Node):    {stat_tags['DFN_Node']}")
    if ENABLE_HETEROGENEOUS:
        print(f"  ● 闭锁抗剪切强结构面 (DFN_Asperity): {stat_tags['DFN_Asperity']}")
        print(f"  ● 一般性基岩摩擦弱面 (DFN_Matrix):    {stat_tags['DFN_Matrix']}")
        print(f"  ● 深厚高滑移断层碎泥 (DFN_Gouge):    {stat_tags['DFN_Gouge']}")
    else:
        print(f"  ● 平层通用弱属性弱面 (DFN_Matrix):    {stat_tags['DFN_Matrix']}")
        
    print(f"  ● 切准并下发状态签的全部颗粒总计:     {sum(stat_tags.values())}")
    print(f"  ● 并发全链路时间开销结算:           {elapsed_time:.3f} 秒")
    print("="*60)
    print(" >>> 地壳破碎再造引擎，使命圆满归宿。")

if __name__ == "__main__":
    main()
