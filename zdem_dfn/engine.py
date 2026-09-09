"""ZDEM DFN 引擎 — 兼容门面（facade）。

v1.1 起引擎拆分为职责单一的下层模块，本文件保留为兼容层：

- ``zdem_dfn.config``     全局常量与开关（运行时覆盖的唯一入口）
- ``zdem_dfn.geometry``   纯几何算法（距离 / 裁剪 / 求交）
- ``zdem_dfn.dfn``        随机裂隙网络生成
- ``zdem_dfn.io``         ini_xyr.dat 解析与带标签输出
- ``zdem_dfn.sampling``   颗粒-裂隙采样与分组
- ``zdem_dfn.plotting``   预览图渲染
- ``zdem_dfn.main``       批处理编排 + CLI

旧代码 ``from zdem_dfn.engine import X`` 继续可用。
注意：运行时覆盖配置请赋值 ``zdem_dfn.config.XXX``（对 engine 属性赋值
不会传播到下层模块）；或直接用 CLI 参数 ``python -m zdem_dfn --dirs ...``。
"""

from zdem_dfn.config import (  # noqa: F401
    CROP_MAX_X,
    CROP_MAX_Y,
    CROP_MIN_X,
    CROP_MIN_Y,
    ENABLE_HETEROGENEOUS,
    ENABLE_NODE_PENALTY,
    FRACTURE_SETS,
    PROB_ASPERITY,
    PROB_GOUGE,
    PROB_MATRIX,
    SOURCE_FILENAME,
    TARGET_DIRECTORIES,
    TARGET_FILENAME,
    FractureValue,
    ParticleValue,
)
from zdem_dfn.geometry import (  # noqa: F401
    BOTTOM,
    INSIDE,
    LEFT,
    RIGHT,
    TOP,
    _compute_outcode,
    clip_line_segment,
    get_segment_intersection,
    point_to_segment_distance,
)
from zdem_dfn.dfn import generate_dfn_network  # noqa: F401
from zdem_dfn.io import (  # noqa: F401
    avg_diameter_of,
    compute_reference_stats,
    output_tagged_coordinates,
    parse_particle_file,
)
from zdem_dfn.sampling import (  # noqa: F401
    check_particles_overlap,
    process_single_folder_lines,
    random_tag_by_probability,
)
from zdem_dfn.plotting import generate_preview_plot  # noqa: F401
from zdem_dfn.main import main, run_batch  # noqa: F401
