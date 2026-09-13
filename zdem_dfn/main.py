"""主控流程：批处理编排 + argparse CLI。

``python -m zdem_dfn`` 的实际入口。默认行为（v1.2 起）**非破坏性**：
带标签颗粒写入 ``<stem><suffix><ext>``（默认 ``ini_xyr_dfn.dat``），
源 ``ini_xyr.dat`` 保持不动；显式传 ``--in-place`` 才恢复旧版覆写语义。
"""

import argparse
import os
import random
import sys
import time

from tqdm import tqdm

from zdem_dfn import config
from zdem_dfn.dfn import generate_dfn_network
from zdem_dfn.io import (
    compute_reference_stats,
    output_tagged_coordinates,
    parse_particle_file,
)
from zdem_dfn.sampling import apply_fracture_tagging

DEFAULT_SUFFIX = "_dfn"


def _derive_output_path(input_path: str, suffix: str) -> str:
    """源文件路径 + 后缀 → 输出路径（``ini_xyr.dat`` + ``_dfn`` → ``ini_xyr_dfn.dat``）。"""
    stem, ext = os.path.splitext(input_path)
    return f"{stem}{suffix}{ext}"


def run_batch(directories: list[str] | None = None,
              out_image: str | None = None,
              seed: int | None = None,
              dry_run: bool = False,
              suffix: str = DEFAULT_SUFFIX,
              in_place: bool = False,
              stats_path: str | None = None,
              rose_path: str | None = None) -> int:
    """批处理编排。

    - directories: None 时读 config.TARGET_DIRECTORIES（支持运行时覆盖）。
    - out_image:   None 时保持旧行为（写 cwd/dfn_preview.png），plotting 内部处理。
    - seed:        非空时先 random.seed，保证输出可复现。
    - dry_run:     只解析与生成网络，不写文件、不渲染。
    - suffix:      输出文件名后缀；in_place=True 时忽略。
    - in_place:    True 时覆写源文件（旧版行为），False 时写 <stem><suffix><ext>。
    - stats_path:  非空时写网络统计报告（.csv → CSV，其余 Markdown）。
    - rose_path:   非空时写极坐标玫瑰图 PNG。

    返回退出码（0 成功；1 配置错误；2 全部目录缺失）。
    """
    print("=" * 60)
    print(" ZDEM DFN 前处理 - 多组系离散裂隙网络批处理")
    print("=" * 60)

    start_time = time.time()

    if seed is not None:
        random.seed(seed)

    dirs = list(directories) if directories is not None else list(config.TARGET_DIRECTORIES)
    if not dirs:
        print("[错误] 目标目录列表为空（config.TARGET_DIRECTORIES 或 --dirs）。")
        return 1

    reference_dir = dirs[0]
    ref_input_file = os.path.join(reference_dir, config.SOURCE_FILENAME)
    if not os.path.isfile(ref_input_file):
        print(f"[错误] 参照目录缺少颗粒文件：{ref_input_file}")
        return 1

    print(f"\n[1/4] 读取参照颗粒文件 {ref_input_file!r} ...")
    ref_stats = compute_reference_stats(ref_input_file)
    if ref_stats is None:
        print(f"[错误] 参照文件无有效颗粒行：{ref_input_file}")
        return 1

    # 与旧引擎一致：分析视野强制采用 config 的 CROP 常量，而非源文件实际范围。
    print(f"    源文件实际范围 => X: {ref_stats['min_x']:.3f}~{ref_stats['max_x']:.3f}, "
          f"Y: {ref_stats['min_y']:.3f}~{ref_stats['max_y']:.3f}")
    min_x: float = config.CROP_MIN_X
    max_x: float = config.CROP_MAX_X
    min_y: float = config.CROP_MIN_Y
    max_y: float = config.CROP_MAX_Y
    print("    已应用 CROP 常量裁剪分析窗口：")
    print(f"    裁剪后工作区 => X: {min_x:.3f}~{max_x:.3f}, Y: {min_y:.3f}~{max_y:.3f}")

    avg_diameter: float = float(ref_stats["avg_diameter"])
    max_r: float = float(ref_stats["max_r"])
    model_area: float = (max_x - min_x) * (max_y - min_y)

    print(f"    平均颗粒直径: {avg_diameter:.6f}")
    print(f"    分析区面积: {model_area:.6f}")

    print("\n[2/4] 生成裂隙网络 ...")
    fractures, num_fractures = generate_dfn_network(
        model_area, min_x, max_x, min_y, max_y, avg_diameter)
    print(f"    已生成 {num_fractures} 条裂隙。")

    if stats_path:
        from zdem_dfn.stats import compute_network_stats, write_stats_report
        net_stats = compute_network_stats(fractures, min_x, max_x, min_y, max_y)
        write_stats_report(net_stats, stats_path)
        print(f"    统计报告已写入：{stats_path}")

    if rose_path:
        from zdem_dfn.plotting import plot_rose_diagram
        plot_rose_diagram(fractures, rose_path)

    print("\n[3/4] 批处理目标目录 ...")
    grid_cell_size: float = avg_diameter * float(config.FRACTURE_SETS[0]["length_mult"]) * 1.5
    last_lines_data = None

    for folder in tqdm(dirs, desc="批处理进度"):
        if not os.path.exists(folder):
            print(f"[跳过] 目录不存在：{folder}")
            continue

        curr_input_path = os.path.join(folder, config.SOURCE_FILENAME)

        if not os.path.isfile(curr_input_path):
            print(f"    [缺失] 目录中无源文件：{curr_input_path}")
            continue

        if in_place:
            curr_output_path = curr_input_path
        else:
            curr_output_path = _derive_output_path(curr_input_path, suffix)

        print(f"\n    >> 处理目录：{folder}")
        print(f"       输出文件：{curr_output_path}")
        lines_data = parse_particle_file(curr_input_path)

        stat_tags = apply_fracture_tagging(lines_data, fractures, grid_cell_size, max_r)
        print(f"       命中裂隙的颗粒总计: {sum(stat_tags.values())}")

        if dry_run:
            print("    [dry-run] 跳过写文件与渲染")
        else:
            output_tagged_coordinates(curr_output_path, lines_data)
            last_lines_data = lines_data
    if dry_run:
        print("\n[收尾] dry-run 完成：未写颗粒文件、未渲染预览图。"
              "（--stats/--rose 等分析输出若指定仍会写出）")
        return 0

    print("\n[4/4] 渲染预览图 ...")
    if last_lines_data is not None:
        from zdem_dfn.plotting import generate_preview_plot
        generate_preview_plot(last_lines_data, fractures,
                              min_x, max_x, min_y, max_y,
                              out_path=out_image)

    elapsed_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"批处理完成，用时 {elapsed_time:.3f} 秒")
    return 0

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="zdem-dfn",
        description="ZDEM 离散裂隙网络前处理：批处理目标目录、生成带标签颗粒文件并渲染预览图。"
                    "默认非破坏性（写 <stem><suffix><ext>），--in-place 才覆写源文件。",
    )
    p.add_argument("--dirs", nargs="+", metavar="DIR",
                   help="目标目录列表（默认读 zdem_dfn.config.TARGET_DIRECTORIES）")
    p.add_argument("--out", default=None, metavar="PATH",
                   help="预览图输出路径（默认当前目录 dfn_preview.png）")
    p.add_argument("--seed", type=int, default=None,
                   help="随机种子，保证输出可复现")
    p.add_argument("--suffix", default=DEFAULT_SUFFIX, metavar="STR",
                   help=f"输出文件名后缀（默认 {DEFAULT_SUFFIX!r}，生成 ini_xyr{DEFAULT_SUFFIX}.dat；"
                        "需与 --in-place 连用才能设为空串）")
    p.add_argument("--in-place", action="store_true",
                   help="覆写源文件（旧版行为；默认写 <stem><suffix><ext>）")
    p.add_argument("--dry-run", action="store_true",
                   help="只解析与生成网络，不写文件、不渲染")
    p.add_argument("--stats", default=None, metavar="PATH",
                   help="写网络统计报告（p21 实际/目标、方向角分布、迹长分布；"
                        ".csv 后缀写 CSV，其余写 Markdown）")
    p.add_argument("--rose", default=None, metavar="PATH",
                   help="写极坐标玫瑰图（裂隙走向分布，PNG）")
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

    if not args.in_place and args.suffix == "":
        parser.error("--suffix 不能为空串（会覆写源文件）；如需覆写请显式传 --in-place")

    return run_batch(
        directories=args.dirs,
        out_image=args.out,
        seed=args.seed,
        dry_run=args.dry_run,
        suffix=args.suffix,
        in_place=args.in_place,
        stats_path=args.stats,
        rose_path=args.rose,
    )


if __name__ == "__main__":
    sys.exit(main())
