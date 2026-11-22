# -*- coding: utf-8 -*-
"""
Treelight Configuration Manager
树木生理学参数与光源配置数据库 / Tree physiological parameters and light source configuration database
"""
import os
import json
import logging
from typing import Dict, List, Optional

# Configure standard logging output / 配置标准日志输出
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ==================================================
# Path safety configuration (user system directory) / 路径安全配置（用户系统目录）
# ==================================================
USER_HOME = os.path.expanduser("~")
CONFIG_DIR = os.path.join(USER_HOME, ".treelight")

# Safely create config directory without failing in read-only environments / 在只读环境中安全跳过目录创建报错
try:
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
except OSError as e:
    logging.warning(f"Config directory unavailable (read-only environment) / 配置目录不可写: {e}")

CONFIG_FILE = os.path.join(CONFIG_DIR, "treelight_config.json")


class ConfigManager:
    """
    Manage tree physiological parameters and light factors with local persistence. / 管理树种生理参数和光源因子，并支持本地持久化保存。
    """
    def __init__(self):
        # 1. Built-in bilingual tree species database (academic name mapping) / 内置中英双语树种数据库（学术标准名称对照）
        self._builtin_species: Dict[str, Dict[str, float]] = {
            "香樟 (Cinnamomum camphora)": {"alpha": 0.072, "Rd": 1.53, "LCP": 23.1, "LSP": 1480},
            "悬铃木 (Platanus × acerifolia)": {"alpha": 0.058, "Rd": 1.08, "LCP": 25.3, "LSP": 1850},
            "广玉兰 (Magnolia grandiflora)": {"alpha": 0.041, "Rd": 0.65, "LCP": 22.1, "LSP": 1150},
            "银杏 (Ginkgo biloba)": {"alpha": 0.038, "Rd": 0.94, "LCP": 33.8, "LSP": 1280},
            "栾树 (Koelreuteria paniculata)": {"alpha": 0.049, "Rd": 0.78, "LCP": 21.3, "LSP": 1420},
            "无患子 (Sapindus mukorossi)": {"alpha": 0.051, "Rd": 0.614, "LCP": 18.5, "LSP": 1360},
            "榉树 (Zelkova serrata)": {"alpha": 0.04, "Rd": 1.30, "LCP": 37.8, "LSP": 1260},
            "朴树 (Celtis sinensis)": {"alpha": 0.071, "Rd": 1.26, "LCP": 19.9, "LSP": 1320},
            "合欢 (Albizia julibrissin)": {"alpha": 0.038, "Rd": 1.30, "LCP": 34.7, "LSP": 1100},
            "默认阔叶树 (Default Broadleaf)": {"alpha": 0.045, "Rd": 0.80, "LCP": 25.0, "LSP": 1200}
        }
        self._species_db: Dict[str, Dict[str, float]] = dict(self._builtin_species)

        # 2. Built-in light source conversion factors / 内置光源转换因子
        self._builtin_lights: Dict[str, float] = {
            "3000K LED": 0.0143,
            "4000K LED": 0.0154,
            "5000K LED": 0.0170,
            "Universal White LED": 0.0150
        }
        self._light_factors: Dict[str, float] = dict(self._builtin_lights)

        # 3. Load the local user-defined configuration at initialization / 初始化时尝试加载本地用户自定义配置文件
        self.load_config()

    def load_config(self) -> None:
        """
        Load the local configuration file. / 读取本地配置文件。
        """
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "species" in data and isinstance(data["species"], dict):
                        self._species_db.update(data["species"])
                    if "color_temp" in data and isinstance(data["color_temp"], dict):
                        self._light_factors.update(data["color_temp"])
            except Exception as e:
                logging.warning(f"Failed to load user config file / 加载用户配置文件失败: {e}")

    def save_config(self) -> None:
        """
        Save the current configuration to a local file. / 保存当前配置到本地文件。
        """
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "species": self._species_db,
                    "color_temp": self._light_factors
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Failed to save config file / 保存配置文件失败: {e}")

    def register_species(self, name: str, alpha: float, rd: float, lcp: float, lsp: Optional[float] = None) -> None:
        """
        Add a custom tree species and persist it automatically. / 添加自定义树种，并自动持久化。
        """
        if not name or not isinstance(name, str):
            raise ValueError("Species name must be a valid string. / 树种名称必须是有效的字符串。")
        if alpha < 0 or rd < 0 or lcp < 0:
            raise ValueError("Physiological parameters cannot be negative. / 生理学参数不能为负数。")

        self._species_db[name] = {
            "alpha": float(alpha),
            "Rd": float(rd),
            "LCP": float(lcp),
            "LSP": float(lsp) if lsp is not None else 0.0
        }
        self.save_config()
        logging.info(f"Species registered successfully / 树种注册成功: {name}")

    def delete_species(self, name: str) -> None:
        """
        Delete a user-defined tree species and update local config. / 删除用户自定义树种并更新本地配置。
        """
        if name not in self._species_db:
            raise ValueError(f"Unknown species '{name}'. / 未知树种 '{name}'。")
        if name in self._builtin_species:
            raise ValueError(f"Built-in species '{name}' cannot be deleted. / 内置默认树种 '{name}' 不可删除。")
        del self._species_db[name]
        self.save_config()
        logging.info(f"Species deleted successfully / 树种删除成功: {name}")

    def register_light(self, name: str, factor: float) -> None:
        """
        Add a custom light source conversion factor and persist it automatically. / 添加自定义光源转换因子，并自动持久化。
        """
        if not name or not isinstance(name, str):
            raise ValueError("Light name must be a valid string. / 光源名称必须是有效的字符串。")
        if factor <= 0:
            raise ValueError("Conversion factor must be strictly positive. / 转换因子必须为正数。")

        self._light_factors[name] = float(factor)
        self.save_config()
        logging.info(f"Light source registered successfully / 光源注册成功: {name}")

    def delete_light(self, name: str) -> None:
        """
        Delete a user-defined light source conversion factor and update local config. / 删除用户自定义光源转换因子并更新本地配置。
        """
        if name not in self._light_factors:
            raise ValueError(f"Unknown light source '{name}'. / 未知光源 '{name}'。")
        if name in self._builtin_lights:
            raise ValueError(f"Built-in light source '{name}' cannot be deleted. / 内置默认光源 '{name}' 不可删除。")
        del self._light_factors[name]
        self.save_config()
        logging.info(f"Light source deleted successfully / 光源删除成功: {name}")

    def get_species(self, name: str) -> Dict[str, float]:
        """
        Get the physiological parameters of the specified species. / 获取指定树种的生理学参数字典。
        """
        if name not in self._species_db:
            valid = list(self._species_db.keys())
            raise ValueError(f"Unknown species '{name}'. Available: {valid} / 未知树种 '{name}'。")
        return self._species_db[name]

    def get_light_factor(self, name: str) -> float:
        """
        Get the PPFD conversion factor of the specified light source. / 获取指定光源的 PPFD 转换因子。
        """
        if name not in self._light_factors:
            valid = list(self._light_factors.keys())
            raise ValueError(f"Unknown light source '{name}'. Available: {valid} / 未知光源 '{name}'。")
        return self._light_factors[name]

    def list_species(self) -> List[str]:
        """
        Return all tree species names. / 返回所有树种名称列表。
        """
        return list(self._species_db.keys())

    def list_lights(self) -> List[str]:
        """
        Return all light source names. / 返回所有光源名称列表。
        """
        return list(self._light_factors.keys())


# ==================================================
# Instantiation and interface exposure / 实例化与接口暴露
# ==================================================
_manager = ConfigManager()

register_species = _manager.register_species
delete_species = _manager.delete_species
register_light = _manager.register_light
delete_light = _manager.delete_light
get_species_params = _manager.get_species
get_ppfd_factor = _manager.get_light_factor
get_available_species = _manager.list_species
get_available_lights = _manager.list_lights
