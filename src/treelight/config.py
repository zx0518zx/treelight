# -*- coding: utf-8 -*-
import os
import json

CONFIG_FILE = "treelight_config.json"

class ConfigManager:
    """
    配置管理器：管理树种生理参数和光源因子，并支持本地持久化保存
    """
    def __init__(self):
        # 1. 内置树种数据库 (对齐至 v5.3 最终版)
        self._species_db = {
            "香樟":   {"alpha": 0.072, "Rd": 1.53, "LCP": 23.1, "LSP": 1480},
            "Platanus × acerifolia": {"alpha": 0.058, "Rd": 1.08, "LCP": 25.3, "LSP": 1850},
            "广玉兰": {"alpha": 0.041, "Rd": 0.65, "LCP": 22.1, "LSP": 1150},
            "银杏":   {"alpha": 0.038, "Rd": 0.94, "LCP": 33.8, "LSP": 1280},
            "栾树":   {"alpha": 0.049, "Rd": 0.78, "LCP": 21.3, "LSP": 1420},
            "无患子": {"alpha": 0.051, "Rd": 0.614, "LCP": 18.5, "LSP": 1360},
            "榉树":   {"alpha": 0.04,  "Rd": 1.30, "LCP": 37.8, "LSP": 1260},
            "朴树":   {"alpha": 0.071, "Rd": 1.26, "LCP": 19.9, "LSP": 1320},
            "合欢":   {"alpha": 0.038, "Rd": 1.30, "LCP": 34.7, "LSP": 1100},
            "default": {"alpha": 0.045, "Rd": 0.80, "LCP": 25.0, "LSP": 1200}
        }

        # 2. 内置光源因子 (对齐至 v5.3 最终版)
        self._light_factors = {
            "3000K LED (0.0143)": 0.0143,
            "4000K LED (0.0154)": 0.0154,
            "5000K LED (0.0170)": 0.0170,
            "Universal White LED (0.0150)": 0.0150
        }

        # 3. 初始化时尝试加载本地配置文件
        self.load_config()

    # --- 持久化接口 ---
    def load_config(self):
        """读取本地配置文件"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "species" in data: 
                        self._species_db.update(data["species"])
                    if "color_temp" in data: 
                        self._light_factors.update(data["color_temp"])
            except Exception as e:
                print(f"⚠️ 配置文件加载失败: {e}")

    def save_config(self):
        """保存当前配置到本地文件"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "species": self._species_db, 
                    "color_temp": self._light_factors
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"⚠️ 配置文件保存失败: {e}")

    # --- 用户接口：添加/修改数据 ---
    def register_species(self, name, alpha, Rd, LCP, LSP=None):
        """用户调用此函数添加自定义树种，并自动持久化"""
        self._species_db[name] = {
            "alpha": float(alpha),
            "Rd": float(Rd),
            "LCP": float(LCP),
            "LSP": float(LSP) if LSP else 0
        }
        self.save_config()  # 添加后立即保存
        print(f"✅ 已注册并保存树种: {name}")

    def register_light(self, name, factor):
        """用户调用此函数添加自定义光源，并自动持久化"""
        self._light_factors[name] = float(factor)
        self.save_config()  # 添加后立即保存
        print(f"✅ 已注册并保存光源: {name}")

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
