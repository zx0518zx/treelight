import numpy as np
from .config import get_species_params

# =========================================================================
# 模块一：碳汇计算 (【核心修改】与 v4.5 脚本对齐)
# =========================================================================
def calculate_implicit_carbon(physics_result, species_name, hours=4380):
    """
    计算隐性碳汇 (Implicit Carbon Sink)
    逻辑与 v4.5 脚本一致：
    1. 仅统计 PPFD > 0.01 的区域 (有效受光面)
    2. 计算增量公式：Gain = alpha * PPFD * Area * Time
    3. 不减去 Rd (呼吸消耗)，因为这是计算人工光带来的"额外"收益
    """
    ppfd = physics_result["ppfd_raw"]
    areas = physics_result["areas"]
    
    # 获取生理参数
    params = get_species_params(species_name)
    alpha = params["alpha"] # AQY 表观量子效率
    
    # 筛选有效区域 (> 0.01)
    mask = ppfd > 0.01
    
    if not np.any(mask):
        return {
            "species": species_name,
            "carbon_g": 0.0,
            "valid_area_ratio": 0.0
        }
    
    # 1. 计算光合通量 (μmol/s)
    # Formula: Flux = Sum( alpha * PPFD_i * Area_i )
    flux_total = np.sum(ppfd[mask] * areas[mask]) * alpha
    
    # 2. 积分计算总碳量 (g)
    # 单位换算：
    # 1e-6: μmol -> mol
    # 44:   mol -> g (CO2)
    # 3600*hours: hours -> seconds
    # 默认 hours = 12 * 365 = 4380
    total_carbon_g = flux_total * 1e-6 * 44 * (hours * 3600)
    
    return {
        "species": species_name,
        "carbon_g": total_carbon_g,
        "valid_area_ratio": np.sum(areas[mask]) / np.sum(areas)
    }