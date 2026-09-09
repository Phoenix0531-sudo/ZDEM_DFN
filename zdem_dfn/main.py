"""主控流程：批处理编排 + argparse CLI。

``python -m zdem_dfn`` 的实际入口。无参数时行为与旧版 ``engine.main()`` 一致：
批处理 config.TARGET_DIRECTORIES、就地覆写颗粒文件、渲染 dfn_preview.png。
"""

import argparse
import os
import random
import sys
import time
from typing import cast

from tqdm import tqdm

from zdem_dfn import config
from zdem_dfn.dfn import generate_dfn_network
from zdem_dfn.io import (
    compute_reference_stats,
    output_tagged_coordinates,
    parse_particle_file,
)
from zdem_dfn.sampling import apply_fracture_tagging


def run_batch(directories: list[str] | None = None,
              out_image: str | None = None,
              seed: int | None = None,
              dry_run: bool = False) -> int:
    """批处理编排（原 main() 的参数化改造）。

    - directories: None 时读 config.TARGET_DIRECTORIES（支持运行时覆盖）。
    - out_image:   None 时保持旧行为（写 cwd/dfn_preview.png），plotting 内部处理。
    - seed:        非空时先 random.seed，保证输出可复现。
    - dry_run:     只解析与生成网络，不写文件、不渲染。

    返回退出码（0 成功；1 配置错误；2 全部目录缺失）。
    """
    print("=" * 60)
    print(" ZDEM 高级离散元就地解析前处理 - 混合多组系 T/X 网络双边引擎")
    print("=" * 60)

    start_time = time.time()

    if seed is not None:
        random.seed(seed)

    dirs = list(directories) if directories is not None else list(config.TARGET_DIRECTORIES)
    if not dirs:
        print("[错误] TARGET_DIRECTORIES 为空，未设防工作簇。")
        return 1

    reference_dir = dirs[0]
    ref_input_file = os.path.join(reference_dir, config.SOURCE_FILENAME)
    if not os.path.isfile(ref_input_file):
        print(f"[严重错误] 未能找到作为基准物理边际刻画的主参照系文件：{ref_input_file}")
        return 1

    print(f"[*] 【全局一阶段】 正在从主坐标系汲取宏观基底场信息 '{ref_input_file}'...")
    ref_stats = compute_reference_stats(ref_input_file)
    if ref_stats is None:
        print("[错误] 未能从参照体系中剥离出微结构颗粒簇。")
        return 1

    # [强行覆盖机制] - 启动核心区绝对裁剪机制（与旧引擎一致）
    print(f"\n[*] 源文件真实检测区域 => X: {ref_stats['min_x']:.3f}~{ref_stats['max_x']:.3f}, "
          f"Y: {ref_stats['min_y']:.3f}~{ref_stats['max_y']:.3f}")
    min_x: float = config.CROP_MIN_X
    max_x: float = config.CROP_MAX_X
    min_y: float = config.CROP_MIN_Y
    max_y: float = config.CROP_MAX_Y
    print("[*] 【强制覆写】已应用 CROP 常量截断矩阵视野至纯核工区：")
    print(f"    -> 裁切后工作区 => X: {min_x:.3f}~{max_x:.3f}, Y: {min_y:.3f}~{max_y:.3f}")

    avg_diameter: float = float(ref_stats["avg_diameter"])
    max_r: float = float(ref_stats["max_r"])
    model_area: float = (max_x - min_x) * (max_y - min_y)

    print(f"    - 参数校勘整体圆球半径均标: {avg_diameter:.6f}")
    print(f"    - 重构后面板二次元面积包围测录值: {model_area:.6f}")

    print("\n[*] 【全局二阶段】 生成全局唯一确定的几何骨架 (Fracture Set)...")
    fractures, num_fractures = generate_dfn_network(
        model_area, min_x, max_x, min_y, max_y, avg_diameter)
    print(f"    - 时空锁定，断层网络已全息投影生成完毕 (共 {num_fractures} 条主干节)。")

    print("\n[*] 【全局三阶段】 进入围岩批次循环系统就地解析...")
    reference_length_base: float = avg_diameter * cast(float, config.FRACTURE_SETS[0]["length_mult"])
    grid_cell_size: float = reference_length_base * 1.5
    last_lines_data = None

    for folder in tqdm(dirs, desc="围压矩阵批处理就地解析"):
        if not os.path.exists(folder):
            print(f"[节点跳过] 找不到指定的围压容器文件夹：{folder}")
            continue

        curr_input_path = os.path.join(folder, config.SOURCE_FILENAME)
        curr_output_path = os.path.join(folder, config.TARGET_FILENAME)

        if not os.path.isfile(curr_input_path):
            print(f"    -> [缺失] 当前矩阵槽内缺乏源文件：{curr_input_path}")
            continue

        print(f"\n    >> 正在切入处理流：{folder}")
        lines_data = parse_particle_file(curr_input_path)

        stat_tags = apply_fracture_tagging(lines_data, fractures, grid_cell_size, max_r)
        print(f"       -> 当地切中有效颗粒总计: {sum(stat_tags.values())}")

        if dry_run:
            print("    -> [dry-run] 跳过写文件与渲染")
        else:
            output_tagged_coordinates(curr_output_path, lines_data)
            last_lines_data = lines_data

    if dry_run:
        print("\n[*] 【收尾】 dry-run 完成，未写任何文件。")
        return 0

    print("\n[*] 【全局四阶段】 影像学构建收尾...")
    if last_lines_data is not None:
        from zdem_dfn.plotting import generate_preview_plot
        generate_preview_plot(last_lines_data, fractures,
                              min_x, max_x, min_y, max_y,
                              out_path=out_image)

    elapsed_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"  ● 地壳破碎再造引擎，批调解析历时总计: {elapsed_time:.3f} 秒")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="zdem-dfn",
        description="ZDEM 离散裂隙网络生成引擎：批处理目标目录、就地覆写颗粒文件并渲染预览图。",
    )
    p.add_argument("--dirs", nargs="+", metavar="DIR",
                   help="目标目录列表（默认读 zdem_dfn.config.TARGET_DIRECTORIES）")
    p.add_argument("--out", default=None, metavar="PATH",
                   help="预览图输出路径（默认当前目录 dfn_preview.png）")
    p.add_argument("--seed", type=int, default=None,
                   help="随机种子，保证输出可复现")
    p.add_argument("--dry-run", action="store_true",
                   help="只解析与生成网络，不写文件、不渲染")
    p.add_argument("--version", action="store_true",
                   help="打印版本号后退出")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.version:
        try:
            from importlib.metadata import version
            print(f"zdem-dfn {version('zdem-dfn')}")
        except Exception:
            print("zdem-dfn (unknown version)")
        return 0

    return run_batch(
        directories=args.dirs,
        out_image=args.out,
        seed=args.seed,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
