"""
TreeLight Initialization Module / TreeLight 初始化模块

This module exposes the public API for the TreeLight package.
本模块暴露 TreeLight 软件包的公共 API 接口。
"""

# Parse IES photometric files 
# 解析 IES 光度文件
from .ies_parser import parse_ies_full

# Configuration and parameter management (e.g., species, lights, PPFD factors)
# 配置与参数管理（例如：树种、光源参数及 PPFD 转换因子）
from .config import (
    register_species, 
    register_light, 
    get_ppfd_factor, 
    get_available_species, 
    get_species_params, 
    get_available_lights
)

# Core spatial light environment analysis and 3D visualization modules
# 核心空间光环境分析与 3D 可视化模块
from .light_analysis import (
    calculate_canopy_ppfd, 
    grade_light_environment, 
    visualize_ppfd_3d
)

# Ecological metrics including potential ALAN-induced carbon fixation index calculations
# 生态学指标计算（包含潜在的人工夜间照明诱导碳固定指数计算）
from .ecology import calculate_implicit_carbon

# Explicitly define public APIs to export
# 明确定义对外导出的公共 API 列表
__all__ = [
    "parse_ies_full",            # Parse IES file data / 解析 IES 文件数据
    "calculate_canopy_ppfd",     # Calculate canopy PPFD / 计算冠层 PPFD 分布
    "grade_light_environment",   # Grade spatial light environment / 空间光环境评级分级
    "visualize_ppfd_3d",         # 3D visualization of canopy PPFD / 冠层 PPFD 的 3D 可视化
    "calculate_implicit_carbon", # Calculate potential carbon index / 计算潜在碳指标
    "register_species",          # Register new tree species parameters / 注册新树种参数
    "register_light",            # Register new light source parameters / 注册新光源参数
    "get_ppfd_factor",           # Get light-specific PPFD conversion factor / 获取特定光源的 PPFD 转换系数
    "get_available_species",     # List all available tree species / 列出所有可用树种
    "get_species_params",        # Retrieve parameters for a specific species / 获取特定树种的具体生理参数
    "get_available_lights"       # List all available light sources / 列出所有可用光源
]

