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


def _ensure_parent(path: str) -> None:
    """Create an artifact's parent directory when needed."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def run_batch(directories: list[str] | None = None,
              out_image: str | None = None,
              seed: int | None = None,
              dry_run: bool = False,
              suffix: str = DEFAULT_SUFFIX,
              in_place: bool = False,
              stats_path: str | None = None,
              rose_path: str | None = None,
              output_dir: str | None = None,
              verbose: bool = False) -> int:
    """批处理编排。

    - directories: None 时读 config.TARGET_DIRECTORIES（支持运行时覆盖）。
    - out_image:   None 时旧接口写 cwd/dfn_preview.png；output_dir 模式写其下的 dfn_preview.png。
    - seed:        非空时先 random.seed，保证输出可复现。
    - dry_run:     只解析与生成网络，不写任何文件、不渲染任何图片。
    - suffix:      输出文件名后缀；in_place=True 时忽略。
    - in_place:    True 时覆写源文件（旧版行为），False 时写 <stem><suffix><ext>。
    - stats_path:  非空时写网络统计报告（.csv → CSV，其余 Markdown）。
    - rose_path:   非空时写极坐标玫瑰图 PNG。
    - output_dir:  单输入目录的安全输出目录；相对报告路径也写入此目录。
    - verbose:     额外打印输入/输出计划；基础进度信息始终保留。

    返回退出码（0 成功；1 配置错误；2 无效参数组合，如空 --suffix 未配 --in-place）。
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
    if output_dir is not None and len(dirs) != 1:
        print("[错误] --output 目录模式只支持一个 --input 目录。")
        return 2
    if output_dir is not None and in_place:
        print("[错误] --output 与 --in-place 不能同时使用。")
        return 2
    if output_dir is not None:
        out_image = out_image or os.path.join(output_dir, "dfn_preview.png")
        if stats_path is not None and not os.path.isabs(stats_path):
            stats_path = os.path.join(output_dir, stats_path)
        if rose_path is not None and not os.path.isabs(rose_path):
            rose_path = os.path.join(output_dir, rose_path)
        if verbose:
            print(f"[verbose] 输入目录：{dirs[0]}")
            print(f"[verbose] 输出目录：{output_dir}")

    reference_dir = dirs[0]
    ref_input_file = os.path.join(reference_dir, config.SOURCE_FILENAME)
    if not os.path.isfile(ref_input_file):
        print(f"[错误] 参照目录缺少颗粒文件：{ref_input_file}")
        return 1

    print(f"\n[1/4] 读取参照颗粒文件 {ref_input_file!r} ...")
    try:
        ref_stats = compute_reference_stats(ref_input_file)
    except (OSError, UnicodeError) as exc:
        print(f"[错误] 无法读取参照文件 {ref_input_file!r}：{exc}")
        return 1
    if ref_stats is None:
        print(f"[错误] 参照文件无有效颗粒行：{ref_input_file}")
        return 1
    if output_dir is not None and not dry_run:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as exc:
            print(f"[错误] 无法创建输出目录 {output_dir!r}：{exc}")
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
        print(f"    统计报告计划路径：{stats_path}")
    if rose_path:
        print(f"    玫瑰图计划路径：{rose_path}")

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
        elif output_dir is not None:
            curr_output_path = _derive_output_path(
                os.path.join(output_dir, os.path.basename(curr_input_path)), suffix)
        else:
            curr_output_path = _derive_output_path(curr_input_path, suffix)

        print(f"\n    >> 处理目录：{folder}")
        print(f"       输出文件：{curr_output_path}")
        try:
            lines_data = parse_particle_file(curr_input_path)
        except (OSError, UnicodeError) as exc:
            print(f"       [错误] 无法读取文件：{exc}")
            continue

        stat_tags = apply_fracture_tagging(lines_data, fractures, grid_cell_size, max_r)
        print(f"       命中裂隙的颗粒总计: {sum(stat_tags.values())}")

        if dry_run:
            print("    [dry-run] 跳过写文件与渲染")
        else:
            try:
                _ensure_parent(curr_output_path)
                output_tagged_coordinates(curr_output_path, lines_data)
            except (OSError, UnicodeError) as exc:
                print(f"       [错误] 无法写出处理结果：{exc}")
                return 1
            last_lines_data = lines_data
    if dry_run:
        print("\n[收尾] dry-run 完成：未创建输出目录，未写颗粒文件、报告或图片。")
        return 0

    if stats_path:
        try:
            _ensure_parent(stats_path)
            from zdem_dfn.stats import compute_network_stats, write_stats_report
            net_stats = compute_network_stats(fractures, min_x, max_x, min_y, max_y)
            write_stats_report(net_stats, stats_path)
            print(f"    统计报告已写入：{stats_path}")
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"[错误] 无法写出统计报告：{exc}")
            return 1

    if rose_path:
        try:
            _ensure_parent(rose_path)
            from zdem_dfn.plotting import plot_rose_diagram
            plot_rose_diagram(fractures, rose_path)
        except (OSError, ValueError) as exc:
            print(f"[错误] 无法写出玫瑰图：{exc}")
            return 1

    print("\n[4/4] 渲染预览图 ...")
    if last_lines_data is not None:
        from zdem_dfn.plotting import generate_preview_plot
        try:
            if out_image is not None:
                _ensure_parent(out_image)
            generate_preview_plot(last_lines_data, fractures,
                                  min_x, max_x, min_y, max_y,
                                  out_path=out_image)
        except (OSError, ValueError) as exc:
            print(f"[错误] 无法写出预览图：{exc}")
            return 1

    elapsed_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"批处理完成，用时 {elapsed_time:.3f} 秒")
    return 0

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="zdem-dfn",
        description="ZDEM DFN 分析工具：读取 ini_xyr.dat，生成带标签颗粒文件和预览图。"
                    "默认非破坏性；只有 --in-place 才会覆写原始文件。",
        epilog="示例：python -m zdem_dfn --input examples/demo_case --output outputs/demo_case\n"
               "检查而不写文件：python -m zdem_dfn --input examples/demo_case "
               "--output outputs/demo_case --dry-run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--input", dest="input_dir", metavar="DIR",
                   help="推荐：单个工况目录，内含 ini_xyr.dat（必须配 --output）")
    p.add_argument("--output", dest="output_dir", metavar="DIR",
                   help="推荐：输出目录（必须配 --input；自动创建，不修改输入目录）")
    p.add_argument("--dirs", nargs="+", metavar="DIR",
                   help="兼容：一个或多个目标目录（默认读 zdem_dfn.config.TARGET_DIRECTORIES）")
    p.add_argument("--out", default=None, metavar="PATH",
                   help="兼容：预览图输出路径（--output 模式自动为 output/dfn_preview.png）")
    p.add_argument("--seed", type=int, default=None,
                   help="随机种子，保证输出可复现")
    p.add_argument("--suffix", default=DEFAULT_SUFFIX, metavar="STR",
                   help=f"输出文件名后缀（默认 {DEFAULT_SUFFIX!r}，生成 ini_xyr{DEFAULT_SUFFIX}.dat；"
                        "需与 --in-place 连用才能设为空串）")
    p.add_argument("--in-place", action="store_true",
                   help="覆写源文件（旧版行为；默认写 <stem><suffix><ext>）")
    p.add_argument("--dry-run", action="store_true",
                   help="只列出输入/输出计划并检查数据，不写任何文件或图片")
    p.add_argument("--verbose", action="store_true",
                   help="打印详细的输入文件、输出文件和跳过原因")
    p.add_argument("--stats", default=None, metavar="PATH",
                   help="写网络统计报告（p21 实际/目标、方向角分布、迹长分布；"
                        ".csv 后缀写 CSV，其余写 Markdown）")
    p.add_argument("--rose", default=None, metavar="PATH",
                   help="写极坐标玫瑰图（裂隙走向分布，PNG）")
    p.add_argument("--version", action="store_true",
                   help="打印版本号后退出")
    return p


def main(argv: list[str] | None = None) -> int:
    # Windows 控制台默认 cp1252/gbk，中文进度输出会 UnicodeEncodeError
    for stream in (sys.stdout, sys.stderr):
        try:
            if stream.encoding and stream.encoding.lower() not in ("utf-8", "utf8"):
                stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, OSError, ValueError):
            pass

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

    if args.input_dir and args.dirs:
        parser.error("--input 与 --dirs 不能同时使用")
    if args.output_dir and args.out:
        parser.error("--output 与 --out 不能同时使用")
    if args.output_dir and not args.input_dir:
        parser.error("--output 必须与 --input 一起使用")
    if args.input_dir and not args.output_dir:
        parser.error("--input 必须与 --output 一起使用；这样可以避免把结果写入输入目录")
    if args.input_dir and args.in_place:
        parser.error("--input 模式不能与 --in-place 一起使用；如需覆写请使用 --dirs")

    directories = [args.input_dir] if args.input_dir else args.dirs
    return run_batch(
        directories=directories,
        out_image=args.out,
        seed=args.seed,
        dry_run=args.dry_run,
        suffix=args.suffix,
        in_place=args.in_place,
        stats_path=args.stats,
        rose_path=args.rose,
        output_dir=args.output_dir,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    sys.exit(main())
