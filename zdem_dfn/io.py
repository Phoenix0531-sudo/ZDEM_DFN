"""文件 IO：解析 ini_xyr.dat 颗粒文件、写出带标签的坐标文件。"""

from typing import cast

from zdem_dfn.config import ParticleValue


def parse_particle_file(input_path: str) -> list[dict[str, ParticleValue]]:
    """读取 ZDEM 颗粒文件，返回结构化行数据（particle / header / empty）。

    解析规则与原 main() 完全一致：一行按空白切分后至少 3 个部分且全部能
    转 float 才算颗粒行，取前三列为 x、y、r；其余非空行原样保留为 header。
    """
    lines_data: list[dict[str, ParticleValue]] = []
    valid_p_count = 0
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            raw = line.rstrip('\n')
            if not raw.strip():
                lines_data.append({"type": "empty", "raw": raw})
                continue
            parts = raw.split()
            if len(parts) >= 3:
                try:
                    x_val = float(parts[0])
                    y_val = float(parts[1])
                    r_val = float(parts[2])

                    # 强行清洗掉历史运行遗留的 Tag 尾巴，只保留 X Y R，并恢复其科学计数法格式，确保其和原始文件保持一致
                    clean_raw = f"{x_val:.12e}  {y_val:.12e}  {r_val:.12e}"

                    valid_p_count += 1
                    lines_data.append({
                        "type": "particle",
                        "raw": clean_raw,  # <--- 使用清洗后的纯净字符串
                        "p_id": valid_p_count,
                        "x": x_val, "y": y_val, "r": r_val,
                        "intersect_count": 0,
                        "tag": None
                    })
                except ValueError:
                    lines_data.append({"type": "header", "raw": raw})
            else:
                lines_data.append({"type": "header", "raw": raw})
    return lines_data


def compute_reference_stats(ref_input_file: str) -> dict[str, float | int] | None:
    """从参照文件计算基准统计量。

    返回 {min_x, max_x, min_y, max_y, max_r, avg_diameter, count}；
    无有效颗粒行返回 None。
    """
    min_x: float = float('inf')
    max_x: float = float('-inf')
    min_y: float = float('inf')
    max_y: float = float('-inf')
    max_r: float = 0.0
    sum_diameter: float = 0.0
    valid_p_count: int = 0

    with open(ref_input_file, encoding="utf-8") as f:
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
        return None

    avg_diameter: float = sum_diameter / valid_p_count
    return {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "max_r": max_r,
        "avg_diameter": avg_diameter,
        "count": valid_p_count,
    }


def avg_diameter_of(parsed: list[dict[str, ParticleValue]]) -> float:
    """从已解析行数据计算平均颗粒直径。"""
    stats = {
        "total": 0.0,
        "count": 0,
    }
    for item in parsed:
        if item.get("type") == "particle":
            stats["total"] += 2.0 * cast(float, item["r"])
            stats["count"] += 1
    if stats["count"] == 0:
        return 0.0
    return stats["total"] / stats["count"]


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
