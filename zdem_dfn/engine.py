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

from tqdm import tqdm
import matplotlib.pyplot as plt  # type: ignore
import matplotlib.collections as mcoll  # type: ignore
from matplotlib.patches import Circle  # type: ignore
from matplotlib.collections import PatchCollection  # type: ignore

# ==========================================
# 模块 1：全局控制开关与宏观参数配置区
# ==========================================

# 核心安全区强制裁剪
CROP_MIN_X = 2000.0
CROP_MAX_X = 6000.0
CROP_MIN_Y = 3000.0
CROP_MAX_Y = 11000.0

# 机制总控开关
ENABLE_HETEROGENEOUS = False          
ENABLE_NODE_PENALTY = False           

SOURCE_FILENAME = "ini_xyr.dat"
TARGET_FILENAME = "ini_xyr.dat"

TARGET_DIRECTORIES = [
    r"E:\0.Information\4.Temp\StructLab\岩石力学部分\DFN\0.N1j纯泥岩\1.DFN\1.5MPa",
    r"E:\0.Information\4.Temp\StructLab\岩石力学部分\DFN\0.N1j纯泥岩\1.DFN\2.10MPa",
    r"E:\0.Information\4.Temp\StructLab\岩石力学部分\DFN\0.N1j纯泥岩\1.DFN\3.20MPa",
    r"E:\0.Information\4.Temp\StructLab\岩石力学部分\DFN\0.N1j纯泥岩\1.DFN\4.40MPa",
    r"E:\0.Information\4.Temp\StructLab\岩石力学部分\DFN\0.N1j纯泥岩\1.DFN\5.60MPa",
    r"E:\0.Information\4.Temp\StructLab\岩石力学部分\DFN\0.N1j纯泥岩\1.DFN\6.80MPa",
]

# 强类型别名使用最新 Python 3.10+ 原生语法 |
FractureValue = str | float
ParticleValue = str | float | int | None

# -------------------------------------------------------------------
# 新特性 2：多组系控制台 (Multiple Fracture Sets)
# -------------------------------------------------------------------
FRACTURE_SETS: list[dict[str, FractureValue]] = [
    {
        "set_name": "Primary_Fault", # 区域性主干断裂 (长且稀疏)
        "p21": 0.002,                
        "length_mult": 15.0,         
        "length_std_ratio": 0.1,     
        "dip_mean": 45.0,            
        "dip_std": 1.0,              
        "truncation_prob": 0.0       
    },
    {
        "set_name": "Secondary_Joints", # 次生微裂隙 (短且极度稀疏)
        "p21": 0.001,                   
        "length_mult": 3.0,             
        "length_std_ratio": 0.3,
        "dip_mean": -45.0,
        "dip_std": 5.0,
        "truncation_prob": 0.90      # 90% 的概率被主断层截断形成 T 型交接
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

def output_tagged_coordinates(output_path: str, lines_data: list[dict[str, ParticleValue]]):
    print(f"[*] 正在追加信息并构建原生坐标输出文件 '{output_path}'...")
    with open(output_path, "w", encoding="utf-8") as f:
        for item in lines_data:
            if item.get("type") == "particle" and item.get("tag") is not None:
                # 触发属性标记的情况，追加 Tab 分隔的后缀字符串
                f.write(str(item["raw"]) + "\t" + str(item["tag"]) + "\n")
            else:
                # 包含不相关的 Header 以及未被切中的游离块情况，原样留存
                f.write(str(item.get("raw", "")) + "\n")

def generate_preview_plot(lines_data: list[dict[str, ParticleValue]], fractures: list[tuple[tuple[float, float], tuple[float, float]]], 
                          min_x: float, max_x: float, min_y: float, max_y: float):
    print("[*] 正在向渲染核心移交可视化图层准备生成预览图...")
    fig, ax = plt.subplots(figsize=(5, 10), dpi=300)  # type: ignore
    
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
            
            circle = Circle((val_x, val_y), val_r)  # type: ignore
            
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
            collection = PatchCollection(items, facecolor=colors_map[key], edgecolor='#A0A0A0', linewidth=0.25, zorder=zorders[key], label=key)  # type: ignore
            ax.add_collection(collection)  # type: ignore

    if fractures:
        segments: list[list[tuple[float, float]]] = []
        for ((cx1, cy1), (cx2, cy2)) in fractures:
            segments.append([(cx1, cy1), (cx2, cy2)])
        lc = mcoll.LineCollection(segments, colors='#8B0000', linewidths=0.8, zorder=6)  # type: ignore
        ax.add_collection(lc)  # type: ignore

    ax.set_aspect('equal')  # type: ignore
    ax.set_xlim(CROP_MIN_X, CROP_MAX_X)  # type: ignore
    ax.set_ylim(CROP_MIN_Y, CROP_MAX_Y)  # type: ignore

    # 学术级坐标轴与刻度精准控制
    ax.set_xticks([3000, 4000, 5000, 6000])  # type: ignore
    ax.set_yticks([3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000])  # type: ignore

    ax.set_xlabel('X (m)', fontsize=12, fontweight='normal')  # type: ignore
    ax.set_ylabel('Y (m)', fontsize=12, fontweight='normal')  # type: ignore
    for spine in ax.spines.values():  # type: ignore
        spine.set_linewidth(1.5)
    ax.tick_params(axis='both', which='major', direction='in', length=6, width=1.5, labelsize=12, top=True, right=True)  # type: ignore
    
    import matplotlib.lines as mlines  # type: ignore
    legend_elements = []  # type: ignore
    for key in ["Background", "DFN_Matrix", "DFN_Asperity", "DFN_Gouge", "DFN_Node"]:
        if plot_dict.get(key):
            legend_elements.append(mlines.Line2D([], [], color=colors_map[key], marker='o', linestyle='None', markersize=10, label=key))  # type: ignore
            
    ax.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=12, frameon=False)  # type: ignore
        
    out_img = os.path.join(os.getcwd(), "dfn_preview.png")
    plt.savefig(out_img, dpi=300, bbox_inches='tight')  # type: ignore
    plt.close(fig)  # type: ignore
    print(f"    - 高品质演示汇报图像已落地：{out_img}")

def main():
    print("="*60)
    print(" ZDEM 高级离散元就地解析前处理 - 混合多组系 T/X 网络双边引擎")
    print("="*60)
    
    start_time = time.time()
    
    if not TARGET_DIRECTORIES:
        print("[错误] TARGET_DIRECTORIES 为空，未设防工作簇。")
        return
        
    reference_dir = TARGET_DIRECTORIES[0]
    ref_input_file = os.path.join(reference_dir, SOURCE_FILENAME)
    if not os.path.exists(ref_input_file):
        print(f"[严重错误] 未能找到作为基准物理边际刻画的主参照系文件：{ref_input_file}")
        return

    print(f"[*] 【全局一阶段】 正在从主坐标系汲取宏观基底场信息 '{ref_input_file}'...")
    min_x: float = float('inf')
    max_x: float = float('-inf')
    min_y: float = float('inf')
    max_y: float = float('-inf')
    max_r: float = 0.0          
    sum_diameter: float = 0.0
    valid_p_count: int = 0
    
    with open(ref_input_file, "r", encoding="utf-8") as f:
        for line in f:
            raw = line.rstrip('\n')
            if not raw.strip():
                continue
            parts = raw.split()
            if len(parts) >= 3:
                try:
                    x_val: float = float(parts[0])
                    y_val: float = float(parts[1])
                    r_val: float = float(parts[2])
                    valid_p_count += 1
                    min_x = min(min_x, x_val)
                    max_x = max(max_x, x_val)
                    min_y = min(min_y, y_val)
                    max_y = max(max_y, y_val)
                    max_r = max(max_r, r_val)
                    sum_diameter += (2.0 * r_val)
                except ValueError:
                    pass

    if valid_p_count == 0:
        print("[错误] 未能从参照体系中剥离出微结构颗粒簇。")
        return

    # [强行覆盖机制] - 启动核心区绝对裁剪机制
    print(f"\n[*] 源文件真实检测区域 => X: {min_x:.3f}~{max_x:.3f}, Y: {min_y:.3f}~{max_y:.3f}")
    min_x = CROP_MIN_X
    max_x = CROP_MAX_X
    min_y = CROP_MIN_Y
    max_y = CROP_MAX_Y
    print(f"[*] 【强制覆写】已应用 CROP 常量截断矩阵视野至纯核工区：")
    print(f"    -> 裁切后工作区 => X: {min_x:.3f}~{max_x:.3f}, Y: {min_y:.3f}~{max_y:.3f}")

    avg_diameter: float = sum_diameter / valid_p_count
    model_width: float = max_x - min_x
    model_height: float = max_y - min_y
    model_area: float = model_width * model_height

    print(f"    - 参数校勘整体圆球半径均标: {avg_diameter:.6f}")
    print(f"    - 重构后面板二次元面积包围测录值: {model_area:.6f}")

    print(f"\n[*] 【全局二阶段】 生成全局唯一确定的几何骨架 (Fracture Set)...")
    fractures, num_fractures = generate_dfn_network(
        model_area, min_x, max_x, min_y, max_y, avg_diameter)
    print(f"    - 时空锁定，断层网络已全息投影生成完毕 (共 {num_fractures} 条主干节)。")

    print("\n[*] 【全局三阶段】 进入围岩批次循环系统就地解析...")
    reference_length_base: float = avg_diameter * cast(float, FRACTURE_SETS[0]["length_mult"])
    grid_cell_size: float = reference_length_base * 1.5
    last_lines_data: list[dict[str, ParticleValue]] | None = None
    
    for folder in tqdm(TARGET_DIRECTORIES, desc="围压矩阵批处理就地解析"):
        if not os.path.exists(folder):
            print(f"[节点跳过] 找不到指定的围压容器文件夹：{folder}")
            continue
            
        curr_input_path = os.path.join(folder, SOURCE_FILENAME)
        curr_output_path = os.path.join(folder, TARGET_FILENAME)
        
        if not os.path.exists(curr_input_path):
            print(f"    -> [缺失] 当前矩阵槽内缺乏源文件：{curr_input_path}")
            continue
            
        print(f"\n    >> 正在切入处理流：{folder}")
        curr_lines_data: list[dict[str, ParticleValue]] = []
        curr_valid_p_count = 0
        
        with open(curr_input_path, "r", encoding="utf-8") as f:
            for line in f:
                raw = line.rstrip('\n')
                if not raw.strip():
                    curr_lines_data.append({"type": "empty", "raw": raw})
                    continue
                parts = raw.split()
                if len(parts) >= 3:
                    try:
                        x_val = float(parts[0])
                        y_val = float(parts[1])
                        r_val = float(parts[2])
                        
                        # 强行清洗掉历史运行遗留的 Tag 尾巴，只保留 X Y R，并恢复其科学计数法格式，确保其和原始文件保持一致
                        clean_raw = f"{x_val:.12e}  {y_val:.12e}  {r_val:.12e}" 
                        
                        curr_valid_p_count += 1
                        curr_lines_data.append({
                            "type": "particle", 
                            "raw": clean_raw,  # <--- 使用清洗后的纯净字符串
                            "p_id": curr_valid_p_count, 
                            "x": x_val, "y": y_val, "r": r_val,
                            "intersect_count": 0,
                            "tag": None
                        })
                    except ValueError:
                        curr_lines_data.append({"type": "header", "raw": raw})
                else:
                    curr_lines_data.append({"type": "header", "raw": raw})
                    
        hash_grid: dict[tuple[int, int], list[int]] = defaultdict(list)
        for idx, p in enumerate(curr_lines_data):
            if p.get("type") == "particle":
                base_px: float = cast(float, p["x"])  
                base_py: float = cast(float, p["y"])  
                base_gx: int = int(base_px // grid_cell_size)  
                base_gy: int = int(base_py // grid_cell_size)  
                hash_grid[(base_gx, base_gy)].append(idx)
                
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
                            target_p = curr_lines_data[p_idx]
                            pt_x: float = cast(float, target_p["x"])  
                            pt_y: float = cast(float, target_p["y"])  
                            pt_r: float = cast(float, target_p["r"])  
                            dist: float = point_to_segment_distance(pt_x, pt_y, x1, y1, x2, y2)
                            if dist <= pt_r: 
                                target_p["intersect_count"] = cast(int, target_p.get("intersect_count", 0)) + 1  
                                
        stat_tags: dict[str, int] = {
            'DFN_Node': 0, 'DFN_Asperity': 0, 'DFN_Matrix': 0, 'DFN_Gouge': 0
        }
        
        for p in curr_lines_data:
            if p.get("type") == "particle":
                intersect_cnt: int = cast(int, p.get("intersect_count", 0)) 
                if intersect_cnt > 0:
                    tag: str | None = None
                    if ENABLE_NODE_PENALTY and intersect_cnt >= 2: 
                        tag = "DFN_Node"
                    else:
                        if ENABLE_HETEROGENEOUS:
                            rand_val: float = random.random()
                            if rand_val < PROB_ASPERITY: tag = "DFN_Asperity"
                            elif rand_val < PROB_ASPERITY + PROB_MATRIX: tag = "DFN_Matrix"
                            else: tag = "DFN_Gouge"
                        else:
                            tag = "DFN_Matrix"
                    p["tag"] = tag
                    if tag is not None:
                        stat_tags[tag] = stat_tags.get(tag, 0) + 1
                        
        print(f"       -> 当地切中有效颗粒总计: {sum(stat_tags.values())}")
        output_tagged_coordinates(curr_output_path, curr_lines_data)
        last_lines_data = curr_lines_data
        
    print("\n[*] 【全局四阶段】 影像学构建收尾...")
    if last_lines_data is not None:
        generate_preview_plot(last_lines_data, fractures, min_x, max_x, min_y, max_y)

    elapsed_time = time.time() - start_time
    print("\n" + "="*60)
    print(f"  ● 地壳破碎再造引擎，批调解析历时总计: {elapsed_time:.3f} 秒")
    print("="*60)

if __name__ == "__main__":
    main()
