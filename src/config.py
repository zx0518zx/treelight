# -*- coding: utf-8 -*-

class ConfigManager:
    """
    配置管理器：管理树种生理参数和光源因子
    """
    def __init__(self):
        # 1. 内置树种数据库 (数据来源：表4-1 长三角地区常见乔木光响应参数表)
        # alpha (AQY): 表观量子效率
        # Rd: 暗呼吸速率 (μmol·m⁻²·s⁻¹)
        # LCP: 光补偿点 (μmol·m⁻²·s⁻¹)
        # LSP: 光饱和点 (μmol·m⁻²·s⁻¹) - 暂存备用
        self._species_db = {
            "香樟": {"alpha": 0.046, "Rd": 0.82, "LCP": 26.5, "LSP": 1480},
            "悬铃木": {"alpha": 0.058, "Rd": 1.12, "LCP": 32.4, "LSP": 1850},
            "广玉兰": {"alpha": 0.041, "Rd": 0.65, "LCP": 22.1, "LSP": 1150},
            "银杏":   {"alpha": 0.038, "Rd": 0.94, "LCP": 35.6, "LSP": 1280},
            "栾树":   {"alpha": 0.049, "Rd": 0.78, "LCP": 21.3, "LSP": 1420},
            "无患子": {"alpha": 0.051, "Rd": 0.72, "LCP": 18.5, "LSP": 1360},
            "鸡爪槭": {"alpha": 0.062, "Rd": 0.45, "LCP": 12.6, "LSP": 785},
            "朴树":   {"alpha": 0.045, "Rd": 1.03, "LCP": 28.4, "LSP": 1320},
            "榉树":   {"alpha": 0.048, "Rd": 0.89, "LCP": 24.6, "LSP": 1260},
            "重阳木": {"alpha": 0.042, "Rd": 0.85, "LCP": 25.8, "LSP": 1180},
            "喜树":   {"alpha": 0.039, "Rd": 0.58, "LCP": 19.2, "LSP": 1050},
            "杨树":   {"alpha": 0.055, "Rd": 1.45, "LCP": 45.2, "LSP": 1950},
            "侧柏":   {"alpha": 0.032, "Rd": 0.61, "LCP": 22.8, "LSP": 980}
        }

        # 2. 内置光源因子
        self._light_factors = {
            "3000K LED": 0.0143,
            "4000K LED": 0.0154,
            "5000K LED": 0.0170,
            "通用白光LED": 0.0150
        }

    # --- 用户接口：添加/修改数据 ---
    def register_species(self, name, alpha, Rd, LCP, LSP=None):
        """用户调用此函数添加自定义树种"""
        self._species_db[name] = {
            "alpha": float(alpha),
            "Rd": float(Rd),
            "LCP": float(LCP),
            "LSP": float(LSP) if LSP else 0
        }
        print(f"✅ 已注册树种: {name}")

    def register_light(self, name, factor):
        """用户调用此函数添加自定义光源"""
        self._light_factors[name] = float(factor)
        print(f"✅ 已注册光源: {name}")

    # --- 内部接口：获取数据 ---
    def get_species(self, name):
        if name not in self._species_db:
            valid = list(self._species_db.keys())
            raise ValueError(f"未知树种 '{name}'。可用树种: {valid}")
        return self._species_db[name]

    def get_light_factor(self, name):
        if name not in self._light_factors:
            valid = list(self._light_factors.keys())
            raise ValueError(f"未知光源 '{name}'。可用光源: {valid}")
        return self._light_factors[name]
    
    def list_species(self):
        return list(self._species_db.keys())

    def list_lights(self):
        return list(self._light_factors.keys())

# 单例模式：全局共享一个配置管理器
_manager = ConfigManager()

# 暴露给外部的函数
register_species = _manager.register_species
register_light = _manager.register_light
get_species_params = _manager.get_species
get_ppfd_factor = _manager.get_light_factor
get_available_species = _manager.list_species
get_available_lights = _manager.list_lights