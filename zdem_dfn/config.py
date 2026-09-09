"""全局控制开关与宏观参数配置区。

运行时覆盖：本模块是所有配置常量的唯一事实来源。需要动态改配置时，
直接对本模块属性赋值（例如 ``zdem_dfn.config.TARGET_DIRECTORIES = [...]``），
或使用 CLI 参数（``python -m zdem_dfn --dirs ...``）。
"""

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
        "set_name": "Primary_Fault",  # 区域性主干断裂 (长且稀疏)
        "p21": 0.002,
        "length_mult": 15.0,
        "length_std_ratio": 0.1,
        "dip_mean": 45.0,
        "dip_std": 1.0,
        "truncation_prob": 0.0,
    },
    {
        "set_name": "Secondary_Joints",  # 次生微裂隙 (短且极度稀疏)
        "p21": 0.001,
        "length_mult": 3.0,
        "length_std_ratio": 0.3,
        "dip_mean": -45.0,
        "dip_std": 5.0,
        "truncation_prob": 0.90,  # 90% 的概率被主断层截断形成 T 型交接
    },
]

PROB_ASPERITY = 0.15
PROB_MATRIX = 0.60
PROB_GOUGE = 0.25


def resolve_directories() -> list[str]:
    """返回当前生效的目标目录列表（始终读取模块属性，支持运行时覆盖）。"""
    return list(TARGET_DIRECTORIES)
